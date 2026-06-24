'use client';

// Persistent, double-buffered (per-move) Zumba avatar player.
//
// Each Zumba move ships its own dedicated GLB. To switch moves with no visible
// delay we preload + GPU-warm one runtime instance per unique move BEFORE the
// session starts, keep them all in a single persistent scene (hidden), and at
// each timeline boundary simply toggle visibility + (re)start that move's mixer.
// No GLB is fetched, parsed, or uploaded to the GPU during active playback, and
// React never remounts the canvas on a move change.

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
} from 'react';
import * as THREE from 'three';
import { ZumbaAssetCache } from '@/lib/zumbaAssetCache';
import type {
  ZumbaMappingsJson,
  ZumbaMoveAsset,
  ZumbaPreloadStatus,
  ZumbaTimelineBlock,
} from '@/lib/zumbaTimelineTypes';

type Phase = 'in' | 'main' | 'out';

export type ZumbaPlayMoveOptions = {
  side?: 'L' | 'R' | null;
  crossfadeMs?: number;
  startAtSeconds?: number;
};

export type ZumbaAvatarPlayerHandle = {
  preloadTimeline(blocks: ZumbaTimelineBlock[]): Promise<void>;
  playMove(moveKey: string, options?: ZumbaPlayMoveOptions): void;
  playIntro(moveKey: string): void;
  playOutro(moveKey: string, onFinished?: () => void): boolean;
  stop(): void;
  getPreloadStatus(): ZumbaPreloadStatus;
};

type ZumbaAvatarPlayerProps = {
  mapping: ZumbaMappingsJson;
  onPreloadStatus?: (status: ZumbaPreloadStatus) => void;
  skinToneColor?: string;
  skinToneStrength?: number;
  cameraDistanceFactor?: number;
  cameraTargetYOffsetFactor?: number;
};

type MoveInstance = {
  container: THREE.Group;
  mixer: THREE.AnimationMixer;
  actions: THREE.AnimationAction[];
  materials: THREE.Material[];
  loop: boolean;
  /** Removes a pending 'finished' listener (e.g. intro -> main handoff). */
  clearFinished?: () => void;
};

const DEFAULT_CROSSFADE_MS = 140;

function clearInstanceFinished(inst: MoveInstance) {
  if (inst.clearFinished) {
    inst.clearFinished();
    inst.clearFinished = undefined;
  }
}

function instanceId(moveKey: string, phase: Phase): string {
  return `${moveKey}:${phase}`;
}

type MatOrig = { transparent: boolean; opacity: number; depthWrite: boolean };

// Fade an instance WITHOUT permanently altering the GLB's authored material
// flags. At full opacity we restore exactly what the asset shipped (so hair /
// eyelashes / mouth render as designed); only mid-crossfade do we force blending.
function setInstanceOpacity(inst: MoveInstance, opacity: number) {
  const clamped = THREE.MathUtils.clamp(opacity, 0, 1);
  for (const m of inst.materials) {
    const mat = m as THREE.Material & {
      opacity: number;
      transparent: boolean;
      depthWrite: boolean;
      userData: { __orig?: MatOrig };
    };
    const orig: MatOrig = mat.userData.__orig ?? {
      transparent: mat.transparent,
      opacity: mat.opacity,
      depthWrite: mat.depthWrite,
    };
    if (!mat.userData.__orig) mat.userData.__orig = orig;

    if (clamped >= 1) {
      mat.transparent = orig.transparent;
      mat.opacity = orig.opacity;
      mat.depthWrite = orig.depthWrite;
    } else {
      mat.transparent = true;
      mat.opacity = orig.opacity * clamped;
      mat.depthWrite = false;
    }
  }
}

function applyDefaultSkinTone(root: THREE.Object3D, color: THREE.Color, strength: number) {
  const s = THREE.MathUtils.clamp(strength, 0, 1);
  if (s <= 0) return;
  root.traverse((child) => {
    if (!(child instanceof THREE.Mesh)) return;
    const materials = Array.isArray(child.material) ? child.material : child.material ? [child.material] : [];
    const meshName = String(child.name || '').toLowerCase();
    for (const mat of materials) {
      const m = mat as THREE.MeshStandardMaterial;
      if (!m || !m.color) continue;
      const matName = String(m.name || '').toLowerCase();
      const looksLikeSkin =
        meshName.includes('body') || meshName.includes('face') || meshName.includes('head') || meshName.includes('skin') ||
        matName.includes('body') || matName.includes('face') || matName.includes('head') || matName.includes('skin');
      if (!looksLikeSkin) continue;
      m.color.lerp(color, s);
      m.needsUpdate = true;
    }
  });
}

// Match Avatar3D's normalizeYogaModelRoot so framing stays consistent with yoga.
function normalizeRoot(root: THREE.Object3D): THREE.Group {
  root.scale.setScalar(1.2);
  root.position.set(0, -1, 0);
  root.updateMatrixWorld(true);

  const box = new THREE.Box3().setFromObject(root);
  const container = new THREE.Group();
  container.add(root);
  if (box.isEmpty()) return container;

  const center = new THREE.Vector3();
  box.getCenter(center);
  container.position.set(-center.x, -box.min.y + 0.5, 0);
  return container;
}

const ZumbaAvatarPlayer = forwardRef<ZumbaAvatarPlayerHandle, ZumbaAvatarPlayerProps>(
  function ZumbaAvatarPlayer(
    {
      mapping,
      onPreloadStatus,
      skinToneColor = '#f3cdac',
      skinToneStrength = 0.45,
      cameraDistanceFactor = 1.65,
      cameraTargetYOffsetFactor = 0.04,
    },
    ref,
  ) {
    const mountRef = useRef<HTMLDivElement>(null);
    const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
    const sceneRef = useRef<THREE.Scene | null>(null);
    const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
    const clockRef = useRef<THREE.Clock>(new THREE.Clock());
    const cacheRef = useRef<ZumbaAssetCache | null>(null);
    const rafRef = useRef<number | null>(null);

    const instancesRef = useRef<Map<string, MoveInstance>>(new Map());
    const activeRef = useRef<MoveInstance | null>(null);
    const crossfadeRef = useRef<{
      from: MoveInstance | null;
      to: MoveInstance;
      start: number;
      duration: number;
    } | null>(null);
    const cameraFittedRef = useRef(false);
    // Bumped every time the scene/renderer is (re)created. React Strict Mode in
    // dev mounts -> unmounts -> mounts, tearing down the first scene; async loads
    // tagged with an old generation are discarded so they don't target a dead scene.
    const sceneGenRef = useRef(0);
    // The last requested preload set, replayed automatically if the scene is rebuilt.
    const pendingBlocksRef = useRef<ZumbaTimelineBlock[] | null>(null);
    const statusRef = useRef<ZumbaPreloadStatus>({ state: 'idle', total: 0, loaded: 0, failed: [] });
    const onPreloadStatusRef = useRef(onPreloadStatus);
    useEffect(() => {
      onPreloadStatusRef.current = onPreloadStatus;
    }, [onPreloadStatus]);

    const emitStatus = (next: Partial<ZumbaPreloadStatus>) => {
      statusRef.current = { ...statusRef.current, ...next };
      onPreloadStatusRef.current?.({ ...statusRef.current });
    };

    function disposeContainer(container: THREE.Object3D) {
      container.traverse((child) => {
        if (!(child instanceof THREE.Mesh)) return;
        try { child.geometry?.dispose(); } catch { /* noop */ }
        const mats = Array.isArray(child.material) ? child.material : child.material ? [child.material] : [];
        for (const m of mats) {
          // Do not dispose texture maps here. Material.clone() keeps texture
          // references shared across clones, and disposing those shared Texture
          // objects per instance can make Three delete WebGL objects from the
          // wrong/lost context after long sessions or remounts.
          try { m.dispose(); } catch { /* noop */ }
        }
      });
      sceneRef.current?.remove(container);
    }

    // --- Scene / renderer setup (persistent for the component lifetime) ---
    useEffect(() => {
      const mount = mountRef.current;
      if (!mount) return;

      sceneGenRef.current += 1;
      cameraFittedRef.current = false;

      const width = mount.clientWidth || 1;
      const height = mount.clientHeight || 1;

      const renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
        failIfMajorPerformanceCaveat: false,
      });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
      renderer.setSize(width, height);
      renderer.setClearColor(0x000000, 0);
      // Match react-three-fiber's defaults (used by Avatar3D). The Avatar3D
      // lighting recipe is tuned for ACES tone mapping; without it the strong
      // lights overexpose every material to solid white.
      renderer.outputColorSpace = THREE.SRGBColorSpace;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1;
      mount.appendChild(renderer.domElement);
      renderer.domElement.style.width = '100%';
      renderer.domElement.style.height = '100%';

      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(50, width / height, 0.01, 1000);
      camera.position.set(0, 0, 3);

      // Lighting recipe mirrors Avatar3D for a consistent look.
      scene.add(new THREE.AmbientLight(0xffffff, 0.95));
      const dir1 = new THREE.DirectionalLight(0xffffff, 1.35);
      dir1.position.set(5, 5, 5);
      scene.add(dir1);
      const dir2 = new THREE.DirectionalLight(0xffffff, 1.1);
      dir2.position.set(-5, 5, 5);
      scene.add(dir2);
      const point = new THREE.PointLight(0xffffff, 0.85);
      point.position.set(0, 2, 2);
      scene.add(point);
      scene.add(new THREE.HemisphereLight(0xffffff, 0x888888, 0.55));

      const cache = new ZumbaAssetCache();
      cache.attachRenderer(renderer);

      rendererRef.current = renderer;
      sceneRef.current = scene;
      cameraRef.current = camera;
      cacheRef.current = cache;

      const handleResize = () => {
        const w = mount.clientWidth || 1;
        const h = mount.clientHeight || 1;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      };
      window.addEventListener('resize', handleResize);
      // The avatar container is resized via CSS (preview <-> session), which does
      // not fire window resize, so observe the element directly.
      const resizeObserver = new ResizeObserver(handleResize);
      resizeObserver.observe(mount);

      // Prevent a transient GPU context loss (driver hiccup, GPU switch) from
      // permanently killing the canvas; three.js re-uploads resources on restore.
      const onContextLost = (e: Event) => e.preventDefault();
      renderer.domElement.addEventListener('webglcontextlost', onContextLost, false);

      clockRef.current.start();
      const instances = instancesRef.current;
      const renderLoop = () => {
        const delta = clockRef.current.getDelta();
        const active = activeRef.current;
        if (active) active.mixer.update(delta);

        // Drive an in-progress opacity crossfade; keep the outgoing move's
        // mixer ticking so it animates while fading out (no frozen pose).
        const cf = crossfadeRef.current;
        if (cf) {
          if (cf.from && cf.from !== active) cf.from.mixer.update(delta);
          const t = THREE.MathUtils.clamp((performance.now() - cf.start) / cf.duration, 0, 1);
          setInstanceOpacity(cf.to, t);
          if (cf.from) setInstanceOpacity(cf.from, 1 - t);
          if (t >= 1) {
            if (cf.from) {
              clearInstanceFinished(cf.from);
              cf.from.container.visible = false;
              try { cf.from.mixer.stopAllAction(); } catch { /* noop */ }
              setInstanceOpacity(cf.from, 1);
            }
            setInstanceOpacity(cf.to, 1);
            crossfadeRef.current = null;
          }
        }

        renderer.render(scene, camera);
        rafRef.current = requestAnimationFrame(renderLoop);
      };
      rafRef.current = requestAnimationFrame(renderLoop);

      return () => {
        sceneGenRef.current += 1;
        window.removeEventListener('resize', handleResize);
        renderer.domElement.removeEventListener('webglcontextlost', onContextLost, false);
        resizeObserver.disconnect();
        if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
        crossfadeRef.current = null;
        for (const inst of instances.values()) {
          clearInstanceFinished(inst);
          try { inst.mixer.stopAllAction(); } catch { /* noop */ }
          disposeContainer(inst.container);
        }
        instances.clear();
        activeRef.current = null;
        try { cache.dispose(); } catch { /* noop */ }
        try { renderer.dispose(); } catch { /* noop */ }
        if (renderer.domElement.parentNode === mount) {
          mount.removeChild(renderer.domElement);
        }
        rendererRef.current = null;
        sceneRef.current = null;
        cameraRef.current = null;
        cacheRef.current = null;
      };
    }, []);

    function fitCameraTo(container: THREE.Group) {
      const camera = cameraRef.current;
      if (!camera) return;
      const box = new THREE.Box3().setFromObject(container);
      if (box.isEmpty()) return;
      const size = new THREE.Vector3();
      const center = new THREE.Vector3();
      box.getSize(size);
      box.getCenter(center);

      const target = center.clone();
      target.y = box.min.y + size.y * (0.5 + cameraTargetYOffsetFactor);
      target.x = 0;

      const distance = size.y * cameraDistanceFactor;
      camera.position.set(target.x, target.y, target.z + distance);
      camera.lookAt(target);
      camera.near = Math.max(0.01, distance / 100);
      camera.far = Math.max(1000, distance * 100);
      camera.updateProjectionMatrix();
      cameraFittedRef.current = true;
    }

    // Build (or reuse) a runtime instance for a move phase, warm it on the GPU.
    // `gen` ties the work to a scene generation; if the scene is rebuilt mid-load
    // the result is discarded instead of being added to a disposed scene.
    async function ensureInstance(asset: ZumbaMoveAsset, phase: Phase, gen: number): Promise<MoveInstance | null> {
      const cache = cacheRef.current;
      if (!cache || gen !== sceneGenRef.current) return null;

      const id = instanceId(asset.key, phase);
      const existing = instancesRef.current.get(id);
      if (existing) return existing;

      const url = asset[phase];
      const loaded = await cache.loadGltf(url);
      // The scene may have been torn down while the GLB was downloading.
      if (gen !== sceneGenRef.current) return null;
      const scene = sceneRef.current;
      const renderer = rendererRef.current;
      const camera = cameraRef.current;
      if (!scene || !renderer || !camera) return null;

      const clone = cache.cloneScene(loaded);
      applyDefaultSkinTone(clone, new THREE.Color(skinToneColor), skinToneStrength);
      const container = normalizeRoot(clone);
      container.visible = false;
      scene.add(container);

      const mixer = new THREE.AnimationMixer(clone);
      const loop = phase === 'main';
      const actions: THREE.AnimationAction[] = [];
      for (const clip of loaded.animations) {
        const action = mixer.clipAction(clip);
        action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce, loop ? Infinity : 1);
        action.clampWhenFinished = !loop;
        actions.push(action);
      }

      const materials: THREE.Material[] = [];
      clone.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          const ms = Array.isArray(child.material) ? child.material : child.material ? [child.material] : [];
          for (const m of ms) if (m) materials.push(m);
        }
      });

      const inst: MoveInstance = { container, mixer, actions, materials, loop };
      instancesRef.current.set(id, inst);

      // GPU warm-up: render two frames with this instance briefly visible so the
      // first real switch doesn't stutter on texture/geometry upload.
      mixer.update(0);
      const prevVisible = container.visible;
      container.visible = true;
      renderer.render(scene, camera);
      renderer.render(scene, camera);
      container.visible = prevVisible;

      if (!cameraFittedRef.current && phase === 'main') {
        fitCameraTo(container);
      }
      return inst;
    }

    // Finalize any crossfade still in flight so a rapid second switch is clean.
    function settleCrossfade() {
      const cf = crossfadeRef.current;
      if (!cf) return;
      if (cf.from && cf.from !== activeRef.current) {
        clearInstanceFinished(cf.from);
        cf.from.container.visible = false;
        try { cf.from.mixer.stopAllAction(); } catch { /* noop */ }
        setInstanceOpacity(cf.from, 1);
      }
      setInstanceOpacity(cf.to, 1);
      crossfadeRef.current = null;
    }

    function showInstance(
      inst: MoveInstance,
      opts?: { startAtSeconds?: number; crossfadeMs?: number; onFinished?: () => void },
    ) {
      settleCrossfade();
      const startAtSeconds = opts?.startAtSeconds ?? 0;
      const crossfadeMs = opts?.crossfadeMs ?? 0;
      const previous = activeRef.current;
      if (previous === inst) {
        // Same instance already on screen (e.g. repeated block of one move):
        // let it keep looping instead of restarting — avoids a visible hitch.
        return;
      }

      // Drop any stale handoff listener still bound to this instance.
      clearInstanceFinished(inst);

      // Start the new instance first so there is never a blank frame.
      for (const action of inst.actions) {
        action.reset();
        if (startAtSeconds > 0) action.time = startAtSeconds;
        action.play();
      }
      if (opts?.onFinished && inst.actions.length > 0) {
        const onFinished = opts.onFinished;
        const handle = (e: { action?: THREE.AnimationAction }) => {
          if (!e.action || !inst.actions.includes(e.action)) return;
          inst.mixer.removeEventListener('finished', handle as never);
          inst.clearFinished = undefined;
          onFinished();
        };
        inst.mixer.addEventListener('finished', handle as never);
        inst.clearFinished = () => inst.mixer.removeEventListener('finished', handle as never);
      }
      inst.container.visible = true;
      activeRef.current = inst;

      if (previous && previous !== inst) {
        if (crossfadeMs > 0) {
          setInstanceOpacity(inst, 0);
          setInstanceOpacity(previous, 1);
          crossfadeRef.current = { from: previous, to: inst, start: performance.now(), duration: crossfadeMs };
        } else {
          clearInstanceFinished(previous);
          previous.container.visible = false;
          try { previous.mixer.stopAllAction(); } catch { /* noop */ }
        }
      } else {
        setInstanceOpacity(inst, 1);
      }
    }

    // Load + GPU-warm everything the selected song/mode needs. Tagged with the
    // current scene generation so a Strict Mode rebuild can safely replay it.
    async function runPreload(blocks: ZumbaTimelineBlock[]) {
      const gen = sceneGenRef.current;
      const uniqueKeys: string[] = [];
      const seen = new Set<string>();
      for (const b of blocks) {
        if (!seen.has(b.moveKey)) {
          seen.add(b.moveKey);
          uniqueKeys.push(b.moveKey);
        }
      }
      if (uniqueKeys.length === 0) {
        emitStatus({ state: 'ready', total: 0, loaded: 0, failed: [] });
        return;
      }

      // Full set: every selected move's in/main/out. We only load the missing
      // instances so switching back to an already-prepared mode feels instant.
      const missing: Array<{ key: string; phase: Phase }> = [];
      for (const key of uniqueKeys) {
        for (const phase of ['in', 'main', 'out'] as Phase[]) {
          if (!instancesRef.current.has(instanceId(key, phase))) {
            missing.push({ key, phase });
          }
        }
      }

      if (missing.length === 0) {
        emitStatus({ state: 'ready', total: 0, loaded: 0, failed: [] });
        const firstMain = instancesRef.current.get(instanceId(uniqueKeys[0], 'main'));
        if (firstMain && !activeRef.current) showInstance(firstMain, {});
        return;
      }

      emitStatus({ state: 'loading', total: missing.length, loaded: 0, failed: [] });
      const failed: string[] = [];
      let loaded = 0;

      for (const item of missing) {
        if (gen !== sceneGenRef.current) return; // superseded by a scene rebuild
        const asset = mapping.moves[item.key];
        if (!asset) {
          failed.push(`${item.key} (missing manifest entry)`);
          emitStatus({ failed: [...failed] });
          continue;
        }
        try {
          await ensureInstance(asset, item.phase, gen);
          loaded += 1;
          emitStatus({ loaded });
        } catch {
          failed.push(asset[item.phase]);
          emitStatus({ failed: [...failed] });
        }
      }

      if (gen !== sceneGenRef.current) return;
      emitStatus({ state: failed.length > 0 ? 'error' : 'ready' });

      // Show the first move as a preview if nothing is playing yet. This keeps
      // the avatar visible after a scene rebuild without relying on the page.
      if (failed.length === 0 && !activeRef.current) {
        const firstMain = instancesRef.current.get(instanceId(uniqueKeys[0], 'main'));
        if (firstMain) showInstance(firstMain, {});
      }
    }

    useImperativeHandle(ref, (): ZumbaAvatarPlayerHandle => ({
      async preloadTimeline(blocks: ZumbaTimelineBlock[]) {
        pendingBlocksRef.current = blocks;
        await runPreload(blocks);
      },

      playMove(moveKey: string, options?: ZumbaPlayMoveOptions) {
        const inst = instancesRef.current.get(instanceId(moveKey, 'main'));
        if (!inst) {
          // Should not happen after a successful preload; keep current move.
          console.warn(`[ZumbaAvatarPlayer] main instance not ready for ${moveKey}`);
          return;
        }
        showInstance(inst, {
          startAtSeconds: options?.startAtSeconds ?? 0,
          crossfadeMs: options?.crossfadeMs ?? DEFAULT_CROSSFADE_MS,
        });
      },

      // Smooth "enter the move" flow: Idle In once, then auto-blend into the
      // looping Main. Used at every move-group boundary so steps never pop in.
      playIntro(moveKey: string) {
        const introInst = instancesRef.current.get(instanceId(moveKey, 'in'));
        const mainInst = instancesRef.current.get(instanceId(moveKey, 'main'));
        if (!introInst) {
          const fallbackInst = instancesRef.current.get(instanceId(moveKey, 'main'));
          if (fallbackInst) {
            showInstance(fallbackInst, { crossfadeMs: DEFAULT_CROSSFADE_MS });
          }
          return;
        }
        showInstance(introInst, {
          crossfadeMs: DEFAULT_CROSSFADE_MS,
          onFinished: () => {
            if (mainInst) showInstance(mainInst, { crossfadeMs: DEFAULT_CROSSFADE_MS });
          },
        });
      },

      playOutro(moveKey: string, onFinished?: () => void) {
        const outInst = instancesRef.current.get(instanceId(moveKey, 'out'));
        if (!outInst) return false;
        showInstance(outInst, { crossfadeMs: DEFAULT_CROSSFADE_MS, onFinished });
        return true;
      },

      stop() {
        const active = activeRef.current;
        if (active) {
          try { active.mixer.stopAllAction(); } catch { /* noop */ }
        }
      },

      getPreloadStatus() {
        return { ...statusRef.current };
      },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- imperative methods read current refs; recreating the handle is unnecessary.
    }), []);

    return <div ref={mountRef} className="h-full w-full" />;
  },
);

export default ZumbaAvatarPlayer;
