'use client';

// Persistent, prewarmed Zumba avatar player.
//
// Each Zumba move ships its own dedicated GLB. To switch moves with no visible
// delay we preload + GPU-warm one runtime instance per unique move BEFORE the
// session starts, keep them all in a single persistent scene (hidden), and at
// each timeline boundary simply toggle visibility + (re)start that move's mixer.
// No GLB is fetched, parsed, or uploaded to the GPU during active playback, and
// React never remounts the canvas on a move change. Model swaps are atomic:
// authored material depth/transparency settings are never changed because the
// avatar's body and clothing are separate layered meshes.

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
  /**
   * Playback speed multiplier from the client's corrected sheet so the Main
   * loop fits the beat window exactly (e.g. 0.992 = 0.8% slower).
   */
  timeScale?: number;
};

export type ZumbaPreloadOptions = {
  /**
   * Beat-corrected timelines switch straight to Main at group boundaries, so
   * only the first move's Idle-In and the last move's Idle-Out are needed.
   * This loads ~1/3 of the models — critical on low-VRAM GPUs.
   */
  corrected?: boolean;
};

export type ZumbaAvatarPlayerHandle = {
  preloadTimeline(blocks: ZumbaTimelineBlock[], opts?: ZumbaPreloadOptions): Promise<void>;
  playMove(moveKey: string, options?: ZumbaPlayMoveOptions): void;
  playIntro(moveKey: string): void;
  /** Beat lead-in: hold on the move's Idle In until the song's count 1. */
  playLeadIn(moveKey: string): void;
  playOutro(moveKey: string, onFinished?: () => void): boolean;
  stop(): void;
  getPreloadStatus(): ZumbaPreloadStatus;
};

// Safety band for sheet-driven speed adjustment; matches the converter.
const TIME_SCALE_MIN = 0.45;
const TIME_SCALE_MAX = 1.15;

// Global visual tempo multiplier applied on top of the sheet's speed scale.
// < 1 slows every animation for a calmer look. NOTE: values other than 1.0
// trade away exact loop-fit at group boundaries (the sheet's loop math
// assumes its speed scale is applied unmodified) — move switches stay
// beat-aligned either way because they are driven by the audio clock.
const ZUMBA_MOTION_TEMPO = 0.85;

// Runtime override so testers can A/B tempo live from the Beat Test panel
// (no rebuild needed). Applies from the next move switch.
export const ZUMBA_TEMPO_STORAGE_KEY = 'zumba.motionTempo';

function currentMotionTempo(): number {
  if (typeof window === 'undefined') return ZUMBA_MOTION_TEMPO;
  const raw = window.localStorage.getItem(ZUMBA_TEMPO_STORAGE_KEY);
  const value = raw ? Number.parseFloat(raw) : Number.NaN;
  return Number.isFinite(value) && value >= 0.5 && value <= 1.2 ? value : ZUMBA_MOTION_TEMPO;
}

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
  loop: boolean;
  /** Removes a pending 'finished' listener (e.g. intro -> main handoff). */
  clearFinished?: () => void;
};

function clearInstanceFinished(inst: MoveInstance) {
  if (inst.clearFinished) {
    inst.clearFinished();
    inst.clearFinished = undefined;
  }
}

// Attach a one-shot 'finished' callback to an instance, replacing any pending one.
function attachFinished(inst: MoveInstance, onFinished: () => void) {
  clearInstanceFinished(inst);
  const handle = (e: { action?: THREE.AnimationAction }) => {
    if (!e.action || !inst.actions.includes(e.action)) return;
    inst.mixer.removeEventListener('finished', handle as never);
    inst.clearFinished = undefined;
    onFinished();
  };
  inst.mixer.addEventListener('finished', handle as never);
  inst.clearFinished = () => inst.mixer.removeEventListener('finished', handle as never);
}

function instanceId(moveKey: string, phase: Phase): string {
  return `${moveKey}:${phase}`;
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
    const cameraFittedRef = useRef(false);
    // Bumped every time the scene/renderer is (re)created. React Strict Mode in
    // dev mounts -> unmounts -> mounts, tearing down the first scene; async loads
    // tagged with an old generation are discarded so they don't target a dead scene.
    const sceneGenRef = useRef(0);
    // The last requested preload set, replayed automatically if the scene is rebuilt.
    const pendingBlocksRef = useRef<ZumbaTimelineBlock[] | null>(null);
    const pendingOptsRef = useRef<ZumbaPreloadOptions | undefined>(undefined);
    // Serializes overlapping preloads (rapid song/mode switching): only the
    // newest run may evict/load; older runs abort at their next checkpoint.
    const preloadRunIdRef = useRef(0);
    // While the GL context is lost, every GPU handle we own is already dead.
    // Calling dispose()/delete on them poisons the restored context
    // ("object does not belong to this context"), so disposal is skipped.
    const contextLostRef = useRef(false);
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

    // Remove one move instance from the scene and release ONLY its cloned
    // materials. Geometries and textures are shared with the asset cache, so
    // they are released separately via cache.evict() once no clone uses them.
    function evictInstance(id: string, inst: MoveInstance) {
      clearInstanceFinished(inst);
      try { inst.mixer.stopAllAction(); } catch { /* noop */ }
      if (activeRef.current === inst) activeRef.current = null;
      sceneRef.current?.remove(inst.container);
      // Skip GL deletes while the context is lost — those handles are dead and
      // deleting them poisons a subsequently restored context.
      if (!contextLostRef.current) {
        inst.container.traverse((child) => {
          if (!(child instanceof THREE.Mesh)) return;
          const mats = Array.isArray(child.material) ? child.material : child.material ? [child.material] : [];
          for (const m of mats) {
            try { m?.dispose(); } catch { /* noop */ }
          }
        });
      }
      instancesRef.current.delete(id);
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
      // permanently killing the canvas.
      const onContextLost = (e: Event) => {
        e.preventDefault();
        contextLostRef.current = true;
        console.warn('[ZumbaAvatarPlayer] WebGL context lost — waiting for restore');
      };
      const onContextRestored = () => {
        console.info('[ZumbaAvatarPlayer] WebGL context restored — rebuilding world');
        // Full clean rebuild. Every GPU handle from the old context is dead;
        // re-using or disposing them corrupts the restored context. Drop all
        // instances + the asset cache WITHOUT any GL deletes, then replay the
        // last preload so the current song/mode reloads fresh.
        sceneGenRef.current += 1;
        for (const inst of instancesRef.current.values()) {
          clearInstanceFinished(inst);
          try { inst.mixer.stopAllAction(); } catch { /* noop */ }
          scene.remove(inst.container);
        }
        instancesRef.current.clear();
        activeRef.current = null;
        cacheRef.current = new ZumbaAssetCache();
        cacheRef.current.attachRenderer(renderer);
        contextLostRef.current = false;
        if (pendingBlocksRef.current && pendingBlocksRef.current.length > 0) {
          void runPreload(pendingBlocksRef.current, pendingOptsRef.current);
        }
      };
      renderer.domElement.addEventListener('webglcontextlost', onContextLost, false);
      renderer.domElement.addEventListener('webglcontextrestored', onContextRestored, false);

      clockRef.current.start();
      const instances = instancesRef.current;
      const renderLoop = () => {
        const delta = clockRef.current.getDelta();
        const active = activeRef.current;
        if (active) active.mixer.update(delta);

        renderer.render(scene, camera);
        rafRef.current = requestAnimationFrame(renderLoop);
      };
      rafRef.current = requestAnimationFrame(renderLoop);

      return () => {
        sceneGenRef.current += 1;
        window.removeEventListener('resize', handleResize);
        renderer.domElement.removeEventListener('webglcontextlost', onContextLost, false);
        renderer.domElement.removeEventListener('webglcontextrestored', onContextRestored, false);
        resizeObserver.disconnect();
        if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
        for (const inst of instances.values()) {
          clearInstanceFinished(inst);
          try { inst.mixer.stopAllAction(); } catch { /* noop */ }
          if (contextLostRef.current) {
            // GPU handles are already dead — GL deletes here would poison a
            // later restored context. Just detach from the scene graph.
            scene.remove(inst.container);
          } else {
            disposeContainer(inst.container);
          }
        }
        instances.clear();
        activeRef.current = null;
        try { cacheRef.current?.dispose(); } catch { /* noop */ }
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

      const inst: MoveInstance = { container, mixer, actions, loop };
      instancesRef.current.set(id, inst);

      // Evaluate the authored first frame before any render. Some exports drive
      // clothing/morph state from animation tracks, so rendering the bind state
      // can expose the body for one frame.
      for (const action of actions) action.play();
      mixer.update(0);
      for (const action of actions) {
        action.stop();
        action.reset();
      }

      // GPU warm-up happens in a private render target. Rendering warm-up frames
      // into the visible canvas can expose an incomplete/bind-state avatar until
      // the next RAF presents the real scene.
      const prevVisible = container.visible;
      const previousTarget = renderer.getRenderTarget();
      const warmupTarget = new THREE.WebGLRenderTarget(2, 2, {
        depthBuffer: true,
        stencilBuffer: false,
      });
      container.visible = true;
      try {
        renderer.setRenderTarget(warmupTarget);
        renderer.render(scene, camera);
      } finally {
        renderer.setRenderTarget(previousTarget);
        container.visible = prevVisible;
        warmupTarget.dispose();
      }

      if (!cameraFittedRef.current && phase === 'main') {
        fitCameraTo(container);
      }
      return inst;
    }

    function showInstance(
      inst: MoveInstance,
      opts?: { startAtSeconds?: number; timeScale?: number; onFinished?: () => void },
    ) {
      const startAtSeconds = opts?.startAtSeconds ?? 0;
      const rawTimeScale = (opts?.timeScale ?? 1) * currentMotionTempo();
      const timeScale = THREE.MathUtils.clamp(rawTimeScale, TIME_SCALE_MIN, TIME_SCALE_MAX);
      const previous = activeRef.current;
      if (previous === inst) {
        // Same instance already on screen (e.g. repeated block of one move):
        // let it keep looping instead of restarting — avoids a visible hitch.
        // Still honour a new beat speed scale (same move, new group) and a
        // requested completion callback.
        for (const action of inst.actions) action.timeScale = timeScale;
        if (opts?.onFinished) {
          const running = inst.actions.some((a) => a.isRunning());
          if (!running) {
            opts.onFinished();
          } else {
            attachFinished(inst, opts.onFinished);
          }
        }
        return;
      }

      // Drop any stale handoff listener still bound to this instance.
      clearInstanceFinished(inst);

      // Start the new instance first so there is never a blank frame.
      for (const action of inst.actions) {
        action.reset();
        action.timeScale = timeScale;
        if (startAtSeconds > 0) action.time = startAtSeconds;
        action.play();
      }
      // Apply the requested animation state while the model is still hidden.
      // The following visible render therefore starts at a fully valid frame.
      inst.mixer.update(0);
      if (opts?.onFinished && inst.actions.length > 0) {
        attachFinished(inst, opts.onFinished);
      }

      // Atomic scene-graph swap. A full-model opacity crossfade is unsafe here:
      // forcing depthWrite=false on separate body/outfit meshes can draw the body
      // over the clothing and produce a brief "naked avatar" frame.
      if (previous && previous !== inst) {
        clearInstanceFinished(previous);
        previous.container.visible = false;
        try { previous.mixer.stopAllAction(); } catch { /* noop */ }
      }
      inst.container.visible = true;
      activeRef.current = inst;
    }

    // Load + GPU-warm everything the selected song/mode needs. Tagged with the
    // current scene generation so a Strict Mode rebuild can safely replay it.
    async function runPreload(blocks: ZumbaTimelineBlock[], opts?: ZumbaPreloadOptions) {
      const gen = sceneGenRef.current;
      const runId = ++preloadRunIdRef.current;
      const isStale = () =>
        gen !== sceneGenRef.current || runId !== preloadRunIdRef.current || contextLostRef.current;

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

      // The minimum phase set per move keeps VRAM small (vital on low-VRAM /
      // integrated GPUs). Corrected timelines switch straight to Main at group
      // boundaries, so mid-song Idle-Ins are never played:
      //   corrected: Main for all + Idle-In for first + Idle-Out for last
      //   legacy:    Idle-In + Main for all + Idle-Out for last
      const firstKey = uniqueKeys[0];
      const lastKey = blocks[blocks.length - 1].moveKey;
      const phasesFor = (key: string): Phase[] => {
        const phases: Phase[] = ['main'];
        if (opts?.corrected ? key === firstKey : true) phases.push('in');
        if (key === lastKey) phases.push('out');
        return phases;
      };
      const wanted = new Set<string>();
      for (const key of uniqueKeys) {
        for (const phase of phasesFor(key)) wanted.add(instanceId(key, phase));
      }

      // Evict everything the new timeline does NOT need. Without this, every
      // song/mode change stacked more skinned models + textures into VRAM
      // until the browser killed the WebGL context (white avatar screen).
      const keepMoves = new Set<string>(uniqueKeys);
      for (const [id, inst] of Array.from(instancesRef.current)) {
        if (!wanted.has(id)) evictInstance(id, inst);
      }
      const cache = cacheRef.current;
      if (cache && !contextLostRef.current) {
        for (const [key, asset] of Object.entries(mapping.moves)) {
          if (!keepMoves.has(key)) {
            cache.evict(asset.in);
            cache.evict(asset.main);
            cache.evict(asset.out);
          } else {
            // Kept move: release the phases this timeline doesn't use.
            const phases = new Set(phasesFor(key));
            if (!phases.has('in')) cache.evict(asset.in);
            if (!phases.has('out')) cache.evict(asset.out);
          }
        }
      }

      // We only load the missing instances so switching back to an
      // already-prepared mode feels instant.
      const missing: Array<{ key: string; phase: Phase }> = [];
      for (const key of uniqueKeys) {
        for (const phase of phasesFor(key)) {
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
        if (isStale()) return; // superseded by a newer preload / scene rebuild
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

      if (isStale()) return;
      emitStatus({ state: failed.length > 0 ? 'error' : 'ready' });

      // Show the first move as a preview if nothing is playing yet. This keeps
      // the avatar visible after a scene rebuild without relying on the page.
      if (failed.length === 0 && !activeRef.current) {
        const firstMain = instancesRef.current.get(instanceId(uniqueKeys[0], 'main'));
        if (firstMain) showInstance(firstMain, {});
      }
    }

    useImperativeHandle(ref, (): ZumbaAvatarPlayerHandle => ({
      async preloadTimeline(blocks: ZumbaTimelineBlock[], opts?: ZumbaPreloadOptions) {
        pendingBlocksRef.current = blocks;
        pendingOptsRef.current = opts;
        await runPreload(blocks, opts);
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
          timeScale: options?.timeScale,
        });
      },

      // Beat lead-in: the song's count 1 is not at 0:00, so hold on the first
      // move's Idle In until the timeline reaches the beat phase offset. The
      // clip plays once and clamps on its final "ready" frame.
      playLeadIn(moveKey: string) {
        const inst =
          instancesRef.current.get(instanceId(moveKey, 'in')) ??
          instancesRef.current.get(instanceId(moveKey, 'main'));
        if (inst) showInstance(inst, {});
      },

      // Smooth "enter the move" flow: Idle In once, then auto-blend into the
      // looping Main. Used at every move-group boundary so steps never pop in.
      playIntro(moveKey: string) {
        const introInst = instancesRef.current.get(instanceId(moveKey, 'in'));
        const mainInst = instancesRef.current.get(instanceId(moveKey, 'main'));
        if (!introInst) {
          const fallbackInst = instancesRef.current.get(instanceId(moveKey, 'main'));
          if (fallbackInst) {
            showInstance(fallbackInst);
          }
          return;
        }
        showInstance(introInst, {
          onFinished: () => {
            if (mainInst) showInstance(mainInst);
          },
        });
      },

      playOutro(moveKey: string, onFinished?: () => void) {
        const outInst = instancesRef.current.get(instanceId(moveKey, 'out'));
        if (!outInst) return false;
        showInstance(outInst, { onFinished });
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
