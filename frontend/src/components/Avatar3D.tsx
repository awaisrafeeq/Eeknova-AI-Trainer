"use client";

import React, { useEffect, useState, useRef, Suspense, useCallback, useLayoutEffect } from "react";

import { Canvas, useFrame, useThree } from "@react-three/fiber";

import * as THREE from "three"

import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";

import { KTX2Loader } from "three/examples/jsm/loaders/KTX2Loader.js";

import * as SkeletonUtils from "three/examples/jsm/utils/SkeletonUtils.js";

// Disable THREE's global loader cache so GLB ArrayBuffers don't pile up in JS heap
// across yoga pose swaps. Browser HTTP cache still handles re-fetches.
THREE.Cache.enabled = false;

// Universal bounding-box floor for yoga sessions. Ensures camera distance stays
// consistent even when a pose's IN-animation first frame has a tight bounding box.
const YOGA_REFERENCE_SIZE = new THREE.Vector3(2.0, 2.2, 1.5);
const useClientLayoutEffect = typeof window !== 'undefined' ? useLayoutEffect : useEffect;

// Module-level cache for static avatar to avoid reload pauses after session ends
let cachedStaticGltf: any = null;
let cachedStaticModelPath: string | null = null;

// Release an HTMLImageElement / ImageBitmap / ImageData held by a texture.
// `texture.dispose()` only frees the GPU upload; the decoded image pixels in JS
// heap are retained via `texture.image` / `texture.source` until those are cleared.
function releaseTextureImage(tex: any) {
  if (!tex) return;
  try {
    const img = tex.image;
    if (img && typeof img.close === 'function') {
      try { img.close(); } catch { } // ImageBitmap
    }
    if (img && 'src' in img) {
      try { img.src = ''; } catch { }
    }
  } catch { }
  try { tex.image = null; } catch { }
  try {
    if (tex.source) {
      tex.source.data = null;
      tex.source = null;
    }
  } catch { }
  try { tex.mipmaps = []; } catch { }
}

// Dispose geometries, materials, and textures of a model to free GPU AND JS-heap memory.
// Models flagged with __isSharedClone share resources with a cached GLTF and are skipped.
function disposeObject3D(obj: any) {
  if (!obj || obj.__isSharedClone) return;
  obj.traverse((child: any) => {
    if (!child.isMesh) return;
    try { child.geometry?.dispose?.(); } catch { }
    const materials = Array.isArray(child.material)
      ? child.material
      : child.material ? [child.material] : [];
    for (const mat of materials) {
      if (!mat) continue;
      // Scan every property for textures — catches custom/plugin maps we'd miss with a fixed list.
      for (const key of Object.keys(mat)) {
        const val = (mat as any)[key];
        if (val && val.isTexture) {
          try { val.dispose(); } catch { }
          releaseTextureImage(val);
        }
      }
      try { mat.dispose?.(); } catch { }
    }
  });
}

function applySkinTone(root: THREE.Object3D, tone: THREE.Color, strength: number) {
  if (!root) return;
  const s = THREE.MathUtils.clamp(strength, 0, 1);
  if (s <= 0) return;
  root.traverse((child: any) => {
    if (!(child instanceof THREE.Mesh)) return;
    const materials = Array.isArray(child.material) ? child.material : child.material ? [child.material] : [];
    if (materials.length === 0) return;
    const meshName = String(child.name || '').toLowerCase();
    for (const mat of materials) {
      if (!mat) continue;
      const matName = String(mat.name || '').toLowerCase();
      const looksLikeSkin =
        meshName.includes('body') ||
        meshName.includes('face') ||
        meshName.includes('head') ||
        meshName.includes('skin') ||
        matName.includes('body') ||
        matName.includes('face') ||
        matName.includes('head') ||
        matName.includes('skin');
      if (!looksLikeSkin) continue;
      if (!mat.color || !(mat.color instanceof THREE.Color)) continue;
      const toneMat = mat as THREE.Material & {
        color: THREE.Color;
        userData?: Record<string, unknown>;
      };
      toneMat.userData = toneMat.userData || {};
      if (!toneMat.userData.__baseSkinColor) {
        toneMat.userData.__baseSkinColor = toneMat.color.clone();
      }
      const baseColor = toneMat.userData.__baseSkinColor as THREE.Color;
      toneMat.color.copy(baseColor).lerp(tone, s);
      mat.needsUpdate = true;
    }
  });
}

function CameraControls({ target }: { target?: [number, number, number] }) {

  const { camera, gl } = useThree();

  const controls = useRef<any>(null);



  useEffect(() => {

    const { OrbitControls } = require("three/examples/jsm/controls/OrbitControls");

    controls.current = new OrbitControls(camera, gl.domElement);

    controls.current.enableDamping = true;

    controls.current.dampingFactor = 0.1;

    controls.current.enableZoom = true;

    controls.current.enablePan = false;

    controls.current.maxPolarAngle = Math.PI / 2;

    if (target) {
      controls.current.target.set(target[0], target[1], target[2]);
      controls.current.update();
    }



    return () => controls.current?.dispose();

  }, [camera, gl, target?.[0], target?.[1], target?.[2]]);



  useFrame(() => controls.current?.update());

  return null;

}

function AutoFitCamera({ object, referenceSize, cameraZoom, cameraTargetYOffset, cameraPositionYRaise, cameraDistanceScale, cameraManualDistanceFactor, cameraManualTargetYOffsetFactor, cameraManualTargetXOffsetFactor, lockCamera, fitTick = 0, onTargetChange }: { object: THREE.Object3D | null; referenceSize: THREE.Vector3 | null; cameraZoom: number; cameraTargetYOffset: number; cameraPositionYRaise?: number; cameraDistanceScale?: number; cameraManualDistanceFactor?: number; cameraManualTargetYOffsetFactor?: number; cameraManualTargetXOffsetFactor?: number; lockCamera?: boolean; fitTick?: number; onTargetChange: (t: [number, number, number]) => void }) {

  const { camera, size, invalidate } = useThree();
  const cameraSetRef = React.useRef(false);
  const appliedFitSignatureRef = React.useRef<string | null>(null);

  // Reset lock when lockCamera prop changes to false
  useEffect(() => {
    if (!lockCamera) {
      cameraSetRef.current = false;
      appliedFitSignatureRef.current = null;
    }
  }, [lockCamera]);

  useClientLayoutEffect(() => {

    if (!object) return;
    if (!Number.isFinite(size.width) || !Number.isFinite(size.height) || size.width < 64 || size.height < 64) {
      return;
    }

    try {

      const box = new THREE.Box3().setFromObject(object);
      const center = new THREE.Vector3();
      const boxSize = new THREE.Vector3();

      box.getCenter(center);
      box.getSize(boxSize);

      const effectiveSize = referenceSize
        ? new THREE.Vector3(
          Math.max(referenceSize.x, boxSize.x),
          Math.max(referenceSize.y, boxSize.y),
          Math.max(referenceSize.z, boxSize.z)
        )
        : boxSize;

      const perspective = camera as THREE.PerspectiveCamera;
      const fitSignature = [
        object.uuid,
        effectiveSize.x.toFixed(3),
        effectiveSize.y.toFixed(3),
        effectiveSize.z.toFixed(3),
        size.width,
        size.height,
        cameraZoom,
        cameraTargetYOffset,
        cameraPositionYRaise ?? 0,
        cameraDistanceScale ?? 1,
        cameraManualDistanceFactor ?? 'auto',
        cameraManualTargetYOffsetFactor ?? 0,
        cameraManualTargetXOffsetFactor ?? 0,
        fitTick,
      ].join('|');

      // Keep the session camera stable for the same fitted model/state, but allow
      // a single refit when animation/model bounds actually change.
      if (lockCamera && cameraSetRef.current && appliedFitSignatureRef.current === fitSignature) {
        return;
      }

      const manualDistanceFactor = Number.isFinite(cameraManualDistanceFactor) && cameraManualDistanceFactor && cameraManualDistanceFactor > 0
        ? cameraManualDistanceFactor
        : null;

      if (manualDistanceFactor) {
        const target = center.clone();
        const manualTargetYOffset = Number.isFinite(cameraManualTargetYOffsetFactor)
          ? cameraManualTargetYOffsetFactor!
          : 0;
        const manualTargetXOffset = Number.isFinite(cameraManualTargetXOffsetFactor)
          ? cameraManualTargetXOffsetFactor!
          : 0;
        // Use the model floor as the primary vertical anchor so framing stays stable
        // across instruction/static and animated in/main/out models whose bbox centers
        // can shift significantly on tall holobox displays.
        const floorAnchoredY = box.min.y + effectiveSize.y * (0.5 + manualTargetYOffset);
        target.y = floorAnchoredY;
        target.x = center.x + effectiveSize.x * manualTargetXOffset;

        const distance = effectiveSize.y * manualDistanceFactor;
        perspective.position.set(target.x, target.y, target.z + distance);
        perspective.lookAt(target);
        perspective.near = Math.max(0.01, distance / 100);
        perspective.far = Math.max(1000, distance * 100);
        perspective.updateProjectionMatrix();
        onTargetChange([target.x, target.y, target.z]);
        invalidate();
        if (lockCamera) {
          cameraSetRef.current = true;
          appliedFitSignatureRef.current = fitSignature;
        }
        return;
      }

      const aspect = size.width / Math.max(1, size.height);
      const vFov = (perspective.fov * Math.PI) / 180;

      const zoom = Number.isFinite(cameraZoom) && cameraZoom > 0 ? cameraZoom : 1;
      const isHighZoom = zoom >= 1.25;

      // Add a bit of headroom so the avatar's head doesn't get cropped on small/portrait canvases.
      // When lockCamera is true (session), use adjusted factor to frame avatar lower without lean
      const baseVerticalFit = aspect < 0.8 ? 0.72 : (isHighZoom ? 0.78 : 0.74);
      const verticalFitFactor = lockCamera ? 0.72 : baseVerticalFit; // 0.72 = even less lean
      const fitHeightDistance = (effectiveSize.y * verticalFitFactor) / Math.tan(vFov * 0.5);
      const hFov = 2 * Math.atan(Math.tan(vFov * 0.5) * aspect);
      const fitWidthDistance = (effectiveSize.x * 0.5) / Math.tan(hFov * 0.5);

      let distance = Math.max(fitHeightDistance, fitWidthDistance);
      const margin = aspect < 0.8 ? 1.55 : 1.2;
      distance *= margin;

      // Zoom the fitted framing without changing the container size.
      distance /= zoom;

      // When zooming in a lot (session), keep extra safety distance so raised hands don't get cropped.
      // This preserves the "bigger avatar" feel while preventing top-edge clipping during animations.
      if (isHighZoom) {
        const zoomSafety = 1 + (zoom - 1.25) * 1.35;
        distance *= Math.max(1, zoomSafety);
      }

      const distanceScale = Number.isFinite(cameraDistanceScale) && cameraDistanceScale && cameraDistanceScale > 0
        ? cameraDistanceScale
        : 1;
      distance *= distanceScale;

      // Bias the target so avatar appears at bottom of viewport during session
      const target = center.clone();
      if (lockCamera) {
        // During session: bias target UP to frame avatar at bottom (0.20 = balance of position and lean)
        target.y += effectiveSize.y * 0.20;
      } else {
        // Normal: slight downward bias for hands
        const biasBase = aspect < 0.8 ? 0.08 : 0.075;
        const biasZoomFactor = zoom >= 1.25 ? 0.05 : (zoom > 1.15 ? 0.2 : 1);
        target.y -= effectiveSize.y * biasBase * biasZoomFactor;
      }

      const yOffset = Number.isFinite(cameraTargetYOffset) ? cameraTargetYOffset : 0;
      target.y += yOffset;

      // Many GLB rigs have an off-center pivot/bounds; keep framing centered horizontally.
      target.x = 0;

      // cameraPositionYRaise: raise camera above target so model appears in lower part of viewport
      const yRaise = Number.isFinite(cameraPositionYRaise) && cameraPositionYRaise ? cameraPositionYRaise * effectiveSize.y : 0;
      
      // To push model to bottom: look at a point ABOVE model's center
      // This makes model appear lower in viewport without changing camera position or model size
      const lookAtTarget = target.clone();
      if (lockCamera) {
        lookAtTarget.y += effectiveSize.y * 0.4; // Look 40% above center = model appears at bottom
      }
      
      perspective.position.set(0, target.y + yRaise, target.z + distance);
      perspective.lookAt(lookAtTarget);
      perspective.near = Math.max(0.01, distance / 100);
      perspective.far = Math.max(1000, distance * 100);
      perspective.updateProjectionMatrix();

      onTargetChange([target.x, target.y, target.z]);
      invalidate();

      // Mark camera as set for lock feature
      if (lockCamera) {
        cameraSetRef.current = true;
        appliedFitSignatureRef.current = fitSignature;
      }

    } catch {

    }

  }, [object, referenceSize, cameraZoom, cameraTargetYOffset, cameraPositionYRaise, cameraDistanceScale, cameraManualDistanceFactor, cameraManualTargetYOffsetFactor, cameraManualTargetXOffsetFactor, lockCamera, camera, size.width, size.height, fitTick, invalidate, onTargetChange]);

  return null;

}



interface PoseAnimation {

  inPath: string;

  mainPath: string;

  outPath: string;

}



const POSE_SPEC: Record<string, { in: number; hold: number; out: number; angle: number }> = {

  "Mountain Pose": { in: 4, hold: 24, out: 5, angle: 90 },

  "Tree Pose": { in: 9, hold: 30, out: 7, angle: 90 },

  "Downward Dog": { in: 9, hold: 30, out: 8, angle: 180 },

  "Warrior 1": { in: 8, hold: 30, out: 6, angle: 270 },

  "Warrior Pose": { in: 8, hold: 30, out: 6, angle: 270 }, // Warrior II

  "Triangle": { in: 4, hold: 25, out: 4, angle: 180 },

  "Child Pose": { in: 10, hold: 33, out: 9, angle: 180 },

  "Cobra Pose": { in: 9, hold: 21, out: 9, angle: 180 },

  "Cat And Camel Pose": { in: 8, hold: 42, out: 10, angle: 180 },

  "Seated Forward": { in: 5, hold: 35, out: 5, angle: 180 },

};



const POSE_ANIMATIONS: Record<string, PoseAnimation> = {

  "Downward Dog": {

    inPath: "/Downward Dog Pose/in_compressed.glb",

    mainPath: "/Downward Dog Pose/main_compressed.glb",

    outPath: "/Downward Dog Pose/out_compressed.glb",

  },
  "Triangle Pose": {
    inPath: "/Triangle Pose/in_compressed.glb",
    mainPath: "/Triangle Pose/main_compressed.glb",
    outPath: "/Triangle Pose/out_compressed.glb",
  },
  "Warrior Pose": {

    inPath: "/Warrior Pose/in_compressed.glb",

    mainPath: "/Warrior Pose/main_compressed.glb",

    outPath: "/Warrior Pose/out_compressed.glb",

  },

  "Mountain Pose": {

    inPath: "/Mountain Pose/in_compressed.glb",

    mainPath: "/Mountain Pose/main_compressed.glb",

    outPath: "/Mountain Pose/out_compressed.glb",

  },

  "Tree Pose": {

    inPath: "/Tree Pose/in_compressed.glb",

    mainPath: "/Tree Pose/main_compressed.glb",

    outPath: "/Tree Pose/out_compressed.glb",

  },

  "Cat And Camel Pose": {

    inPath: "/Cat And Camel Pose/in_compressed.glb",

    mainPath: "/Cat And Camel Pose/main_compressed.glb",

    outPath: "/Cat And Camel Pose/out_compressed.glb",

  },

  "Child Pose": {

    inPath: "/Child Pose/in_compressed.glb",

    mainPath: "/Child Pose/main_compressed.glb",

    outPath: "/Child Pose/out_compressed.glb",

  },

  "Cobra Pose": {

    inPath: "/Cobra Pose/in_compressed.glb",

    mainPath: "/Cobra Pose/main_compressed.glb",

    outPath: "/Cobra Pose/out_compressed.glb",

  },

  "Seated Forward": {

    inPath: "/Seated Forward Pose/in_compressed.glb",

    mainPath: "/Seated Forward Pose/main_compressed.glb",

    outPath: "/Seated Forward Pose/out_compressed.glb",

  },

  "Warrior 1": {

    inPath: "/Warrior 1 Pose/warrior_1_in_compressed.glb",

    mainPath: "/Warrior 1 Pose/warrior_1_main_compressed.glb",

    outPath: "/Warrior 1 Pose/warrior_1_out_compressed.glb",

  },

};



interface Avatar3DProps {
  selectedPose?: string;
  onlyInAnimation?: boolean;
  onlyOutAnimation?: boolean;
  disablePoseMotion?: boolean;
  isTTSSpeaking?: boolean;
  isPaused?: boolean;
  staticMode?: boolean;
  staticModelPath?: string;
  playAnimationPath?: string;
  playAnimationKey?: number;
  cameraZoom?: number;
  cameraTargetYOffset?: number;
  cameraPositionYRaise?: number;
  cameraDistanceScale?: number;
  cameraManualDistanceFactor?: number;
  cameraManualTargetYOffsetFactor?: number;
  cameraManualTargetXOffsetFactor?: number;
  lockCamera?: boolean;
  skinToneColor?: string;
  skinToneStrength?: number;
  onTTSSpeaking?: (speaking: boolean) => void;
  onError?: (error: string) => void;
  onSessionEnd?: () => void;
  onPhaseChange?: (phase: 'in' | 'main' | 'out') => void; // New prop to notify parent of phase changes
  assistantModeActive?: boolean;
  onModelLoaded?: (model: THREE.Object3D | null) => void;
}

function YogaModel({ selectedPose, onlyInAnimation = false, onlyOutAnimation = false, disablePoseMotion = false, isTTSSpeaking = false, isPaused = false, staticMode = false, staticModelPath, playAnimationPath, playAnimationKey, skinToneColor = '#d9a07f', skinToneStrength = 0.28, onError, onTTSSpeaking, onSessionEnd, onPhaseChange, onModelLoaded, onLoadingChange }: Avatar3DProps & { onLoadingChange?: (loading: boolean) => void }) {

  const [model, setModel] = useState<THREE.Group | null>(null);

  const [mixer, setMixer] = useState<THREE.AnimationMixer | null>(null);

  const [currentAnimation, setCurrentAnimation] = useState<'in' | 'main' | 'out'>('in');

  const meshRef = useRef<THREE.Group>(null);

  const animationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const animationFinishedCleanupRef = useRef<(() => void) | null>(null);

  const currentPoseRef = useRef<string>('');

  const scene = useThree((state) => state.scene); // Get scene from useThree hook
  const gl = useThree((state) => state.gl);

  const dracoLoaderRef = useRef<DRACOLoader | null>(null);
  const ktx2LoaderRef = useRef<KTX2Loader | null>(null);

  useEffect(() => {
    if (!dracoLoaderRef.current) {
      const draco = new DRACOLoader();
      draco.setDecoderPath('/draco/');
      dracoLoaderRef.current = draco;
    }
    if (!ktx2LoaderRef.current && gl) {
      const ktx2 = new KTX2Loader().setTranscoderPath('/basis/').detectSupport(gl);
      ktx2LoaderRef.current = ktx2;
    }

    return () => {
      if (ktx2LoaderRef.current) {
        try {
          ktx2LoaderRef.current.dispose();
        } catch { }
      }
      ktx2LoaderRef.current = null;

      if (dracoLoaderRef.current) {
        try {
          dracoLoaderRef.current.dispose();
        } catch { }
      }
      dracoLoaderRef.current = null;
    };
  }, [gl]);

  // Dispose previous model's GPU resources when a new one replaces it.
  // This prevents textures/geometries/materials from accumulating across
  // pose phase swaps (in → main → out) which would otherwise hit 1GB+ in a session.
  useEffect(() => {
    const captured = model;
    return () => {
      if (captured && !(captured as any).__isSharedClone) {
        disposeObject3D(captured);
      }
    };
  }, [model]);

  // Stop the previous AnimationMixer when replaced so its actions/listeners don't leak.
  useEffect(() => {
    const captured = mixer;
    return () => {
      if (captured) {
        try { captured.stopAllAction(); } catch { }
      }
    };
  }, [mixer]);

  useEffect(() => {
    const onAssistantAudio = (ev: Event) => {
      try {
        const detail = (ev as CustomEvent).detail as any;
        if (!detail) return;
        const lvl = typeof detail.level === 'number' ? detail.level : 0;
        assistantAudioLevelRef.current = Math.max(0, Math.min(1, lvl));
        assistantSpeakingRef.current = !!detail.isSpeaking;
      } catch { }
    };

    window.addEventListener('eeknova-assistant-audio', onAssistantAudio as any);
    return () => window.removeEventListener('eeknova-assistant-audio', onAssistantAudio as any);
  }, []);



  // TTS blendshape animation

  const blendshapeMeshRef = useRef<THREE.Mesh | null>(null);

  const blendshapeNamesRef = useRef<string[]>([]);

  const cachedChessClipsRef = useRef<THREE.AnimationClip[] | null>(null);

  const originalBlendshapesRef = useRef<number[]>([]);

  const assistantAudioLevelRef = useRef<number>(0);
  const assistantSpeakingRef = useRef<boolean>(false);
  const blinkPhaseRef = useRef<number>(0);
  const speechEnvelopeRef = useRef<number>(0);
  const speechSeedRef = useRef<number>(Math.random() * 1000);
  const jawBoneRef = useRef<THREE.Bone | null>(null);
  const didLogAssistantDriverRef = useRef(false);

  const detectBlendshapeMesh = useCallback((root: THREE.Object3D) => {
    try {
      let best: THREE.Mesh | null = null;
      let bestScore = -1;
      root.traverse((child: any) => {
        if (!(child instanceof THREE.Mesh)) return;
        const influences = child.morphTargetInfluences;
        if (!influences || influences.length === 0) return;
        const dict = child.morphTargetDictionary || {};
        const names = Object.keys(dict);
        const hasJaw = names.some((n) => n.toLowerCase() === 'jawopen' || n.toLowerCase().includes('jawopen'));
        const hasMouth = names.some((n) => n.toLowerCase().includes('mouth'));
        const hasViseme = names.some((n) => n.toLowerCase().includes('viseme'));
        const score = (hasJaw ? 1000 : 0) + (hasViseme ? 200 : 0) + (hasMouth ? 100 : 0) + influences.length;
        if (score > bestScore) {
          bestScore = score;
          best = child as THREE.Mesh;
        }
      });

      const mesh = best as any;
      if (mesh && mesh.morphTargetInfluences && mesh.morphTargetInfluences.length > 0) {
        blendshapeMeshRef.current = mesh as THREE.Mesh;
        blendshapeNamesRef.current = mesh.morphTargetDictionary ? Object.keys(mesh.morphTargetDictionary) : [];
        originalBlendshapesRef.current = [...(mesh.morphTargetInfluences || [])];
        console.log('[Avatar3D] blendshape mesh selected:', mesh.name, 'count:', blendshapeNamesRef.current.length);
      }
    } catch { }
  }, []);

  const findJawBone = useCallback((root: THREE.Object3D) => {
    try {
      let found: THREE.Bone | null = null;
      root.traverse((child: any) => {
        if (found) return;
        const name = String(child?.name || '').toLowerCase();
        if (child && child.isBone && (name.includes('jaw') || name.includes('mandible'))) {
          found = child as THREE.Bone;
        }
      });
      jawBoneRef.current = found;
    } catch {
      jawBoneRef.current = null;
    }
  }, []);



  // Load chess avatar without animations

  const loadChessAvatar = async (modelPath?: string) => {

    try {

      onLoadingChange?.(true);

      const loader = new GLTFLoader();



      // Set up shared DRACO/KTX2 loaders (avoid repeated loader creation)
      if (dracoLoaderRef.current) loader.setDRACOLoader(dracoLoaderRef.current);
      if (ktx2LoaderRef.current) loader.setKTX2Loader(ktx2LoaderRef.current);



      console.log('Loading static avatar...');

      const actualModelPath = modelPath || 'Idle Breathing Loop_compressed.glb';

      // Use cached GLTF if available for the same model path
      let gltf: any;
      if (cachedStaticGltf && cachedStaticModelPath === actualModelPath) {
        console.log('Using cached static avatar');
        gltf = cachedStaticGltf;
      } else {
        // Load yoga avatar as static model (use in animation)
        gltf = await loader.loadAsync(actualModelPath);
        cachedStaticGltf = gltf;
        cachedStaticModelPath = actualModelPath;
        console.log('Static avatar cached for future use');
      }

      // Clone the scene with deep clone for SkinnedMesh support
      const loadedModel = SkeletonUtils.clone(gltf.scene) as THREE.Group;
      // Mark as shared: its geometries/materials/textures come from cachedStaticGltf
      // and must not be disposed when this clone is removed from the scene.
      (loadedModel as any).__isSharedClone = true;



      // Set shadows and materials

      loadedModel.traverse((child: THREE.Object3D) => {

        if (child instanceof THREE.Mesh) {

          child.castShadow = true;

          child.receiveShadow = true;

          if (child.material) {

            const material = Array.isArray(child.material) ? child.material[0] : child.material;

            if (material && material.map) {

              material.map.anisotropy = 4; // Use fixed value instead of gl.capabilities

              material.map.needsUpdate = true;

            }

          }

        }

      });



      // Position and scale the model

      loadedModel.position.set(0, -1, 0);

      loadedModel.scale.setScalar(1.2);



      // Add to scene

      if (meshRef.current) {

        scene.remove(meshRef.current);

      }

      scene.add(loadedModel);

      meshRef.current = loadedModel;

      setModel(loadedModel);

      onModelLoaded?.(loadedModel);

      onLoadingChange?.(false);

      applySkinTone(loadedModel, new THREE.Color(skinToneColor), skinToneStrength);

      findJawBone(loadedModel);

      detectBlendshapeMesh(loadedModel);

      detectBlendshapeMesh(loadedModel);

      console.log('Static avatar loaded successfully');



      // Create animation mixer and play animation if available

      const animationMixer = new THREE.AnimationMixer(loadedModel);

      setMixer(animationMixer);



      // Play animation if available AND not a chess avatar

      if (gltf.animations && gltf.animations.length > 0) {

        // Don't auto-play animations for chess avatars

        const isChessAvatar = staticModelPath && staticModelPath.includes('Encouraging Gesture');

        if (isChessAvatar) {
          cachedChessClipsRef.current = gltf.animations;
        }

        if (!isChessAvatar) {

          console.log('🎭 Found animations:', gltf.animations.map((a: THREE.AnimationClip) => a.name));



          gltf.animations.forEach((clip: THREE.AnimationClip) => {

            const action = animationMixer.clipAction(clip);

            action.setLoop(THREE.LoopOnce, 1);

            action.clampWhenFinished = true;

            action.play();

            console.log(`⏹️ Static animation set to play once: ${clip.name}`);

          });

        } else {

          console.log('🎭 Chess avatar - skipping auto-play animations');

        }

      } else {

        console.log('No animations found in static model');

      }

    } catch (error) {

      onLoadingChange?.(false);
      console.error('Error loading static avatar:', error);

      onError?.('Failed to load static avatar');

    }

  };



  useEffect(() => {

    // If static mode or staticModelPath is provided, load static model
    if (staticMode || staticModelPath) {
      // Stop any running animation mixer when switching to static mode
      if (mixer) {
        mixer.stopAllAction();
      }
      // Clear any pending animation timeouts
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current);
        animationTimeoutRef.current = null;
      }
      if (animationFinishedCleanupRef.current) {
        animationFinishedCleanupRef.current();
        animationFinishedCleanupRef.current = null;
      }
      loadChessAvatar(staticModelPath);
      return;
    }



    // Clear any existing timeout

    if (animationTimeoutRef.current) {

      clearTimeout(animationTimeoutRef.current);

    }
    if (animationFinishedCleanupRef.current) {
      animationFinishedCleanupRef.current();
      animationFinishedCleanupRef.current = null;
    }



    if (!selectedPose || !POSE_ANIMATIONS[selectedPose]) {

      console.log('No pose or animation found for:', selectedPose);

      return;

    }



    console.log('Loading pose:', selectedPose);



    // Always reload animation when pose changes (including restart)

    currentPoseRef.current = selectedPose;



    const pose = POSE_ANIMATIONS[selectedPose];

    const loader = new GLTFLoader();



    // Set up shared DRACO/KTX2 loaders (avoid repeated loader creation)
    if (dracoLoaderRef.current) loader.setDRACOLoader(dracoLoaderRef.current);
    if (ktx2LoaderRef.current) loader.setKTX2Loader(ktx2LoaderRef.current);



    // Start animation sequence only if not in onlyInAnimation mode and not staticMode

    if (staticMode) {

      console.log(`Static mode enabled for ${selectedPose} - loading static model only`);

      loadStaticModel();

      return;

    } else if (onlyOutAnimation) {

      console.log(`Animation should play for ${selectedPose} (onlyOutAnimation=true)`);

      // Play OUT animation when onlyOutAnimation is true

      playAnimationSequence(pose, 'out');

      return;

    } else if (onlyInAnimation) {

      console.log(`Animation should play for ${selectedPose} (onlyInAnimation=true)`);

      // Play animation when onlyInAnimation is true

      playAnimationSequence(pose, 'in');

      return;

    } else {

      // For onlyInAnimation=false, play animation directly (home/dashboard pages)

      console.log(`Avatar loaded for ${selectedPose} and animation will play (onlyInAnimation=false)`);

      playAnimationSequence(pose, 'in');

      return;

    }



    async function loadStaticModel() {

      try {

        onLoadingChange?.(true);
        console.log('Loading static avatar...');



        // Set up loader with proper configuration

        const loader = new GLTFLoader();



        // Set up shared DRACO/KTX2 loaders (avoid repeated loader creation)
        if (dracoLoaderRef.current) loader.setDRACOLoader(dracoLoaderRef.current);
        if (ktx2LoaderRef.current) loader.setKTX2Loader(ktx2LoaderRef.current);

        console.log('Loading static avatar...');



        // Load yoga avatar as static model (use in animation)

        const gltf = await loader.loadAsync('/Mountain Pose/in_compressed.glb');

        const loadedModel = gltf.scene;



        // Set shadows and materials

        loadedModel.traverse((child: THREE.Object3D) => {

          if (child instanceof THREE.Mesh) {

            child.castShadow = true;

            child.receiveShadow = true;

            if (child.material) {

              const material = Array.isArray(child.material) ? child.material[0] : child.material;

              if (material && material.map) {

                material.map.anisotropy = 4;

              }

            }

          }

        });



        // Position and scale the model

        loadedModel.position.set(0, -1, 0);

        loadedModel.scale.setScalar(1.2);



        // Add to scene

        if (meshRef.current) {

          scene.remove(meshRef.current);

        }

        scene.add(loadedModel);

        meshRef.current = loadedModel;

        setModel(loadedModel);
        onModelLoaded?.(loadedModel);

        onLoadingChange?.(false);

        console.log('Static avatar loaded successfully');



        // Create animation mixer and play animation if available

        const animationMixer = new THREE.AnimationMixer(loadedModel);

        setMixer(animationMixer);



        // Play animation if available

        if (gltf.animations && gltf.animations.length > 0) {

          console.log(' Found animations:', gltf.animations.map(a => a.name));



          gltf.animations.forEach((clip: THREE.AnimationClip) => {

            const action = animationMixer.clipAction(clip);

            action.setLoop(THREE.LoopOnce, 1);

            action.clampWhenFinished = true;

            action.play();

            console.log(` Static animation set to play once: ${clip.name}`);

          });

        } else {

          console.log('No animations found in static model');

        }



      } catch (error) {

        onLoadingChange?.(false);
        console.error('Error loading static avatar:', error);

      }

    }



    async function playAnimationSequence(pose: PoseAnimation, type: 'in' | 'main' | 'out') {

      try {

        // Preserve current rotation across in/main/out model swaps
        const previousRotationY = meshRef.current?.rotation.y ?? 0;

        // Signal loading when no model is loaded yet (initial load for any phase)
        if (!model) {
          onLoadingChange?.(true);
        }

        const loadPath = type === 'in' ? pose.inPath : type === 'main' ? pose.mainPath : pose.outPath;
        const gltf = await new Promise<any>((resolve, reject) => {
          loader.load(loadPath, resolve, undefined, reject);
        });

        // Capture the previous phase's model so we can dispose it AFTER the new one
        // has been committed to the scene. Disposing before the swap would leave the
        // renderer briefly drawing with freed textures.
        const previousModel = meshRef.current;

        const loadedModel = gltf.scene;

        // Apply previous rotation immediately so we don't snap back to front-facing (90deg)
        loadedModel.rotation.y = previousRotationY;

        applySkinTone(loadedModel, new THREE.Color(skinToneColor), skinToneStrength);

        // Only cache clips for the chess static-model replay path. Caching yoga pose
        // clips here would pin ~15-25 MB of keyframe data per session permanently.
        if (
          staticModelPath &&
          !cachedChessClipsRef.current &&
          gltf.animations &&
          gltf.animations.length > 0
        ) {
          cachedChessClipsRef.current = gltf.animations;
        }

        // Set up animation mixer

        const animationMixer = new THREE.AnimationMixer(loadedModel);
        setMixer(animationMixer);

        // Find blendshapes for mouth animation - prefer main face, but fall back to any mesh with morph targets
        loadedModel.traverse((child: THREE.Object3D) => {
          if (child instanceof THREE.Mesh && child.morphTargetInfluences && child.morphTargetInfluences.length > 0) {
            // Prioritize body_1 mesh (main face) over mouth meshes
            const childName = child.name.toLowerCase();
            const isMainFaceMesh = childName === 'body_1';
            const isMouthMesh = childName.includes('mouth') ||
              childName.includes('lip') ||
              childName.includes('tongue') ||
              childName.includes('teeth');

            // Update blendshape mesh if this is the main face mesh or has more blendshapes
            if (
              isMainFaceMesh ||
              (isMouthMesh && !blendshapeMeshRef.current) ||
              (!blendshapeMeshRef.current) ||
              (child.morphTargetInfluences && child.morphTargetInfluences.length > (blendshapeMeshRef.current?.morphTargetInfluences?.length || 0))
            ) {
              blendshapeMeshRef.current = child;

              // Get blendshape names
              if (child.morphTargetDictionary) {
                blendshapeNamesRef.current = Object.keys(child.morphTargetDictionary);
              } else {
                blendshapeNamesRef.current = [];
                for (let i = 0; i < (child.morphTargetInfluences?.length || 0); i++) {
                  blendshapeNamesRef.current.push(`${child.name}_blendshape_${i}`);
                }
              }

              // Store original blendshape values
              originalBlendshapesRef.current = [...(child.morphTargetInfluences || [])];
            }
          }
        });

        if (blendshapeMeshRef.current && blendshapeNamesRef.current.length > 0) {
          console.log(
            '[Avatar3D] blendshape mesh selected:',
            blendshapeMeshRef.current.name,
            'count:',
            blendshapeNamesRef.current.length
          );
        }

        detectBlendshapeMesh(loadedModel);

        // Debug: Log all mesh names to understand the structure

        const meshNames: string[] = [];

        loadedModel.traverse((child: THREE.Object3D) => {

          if (child instanceof THREE.Mesh) {

            meshNames.push(child.name);

          }

        });

        // console.log('Available meshes:', meshNames);



        // Play animations

        if (gltf.animations && gltf.animations.length > 0) {

          let maxDuration = 0;

          const playedActions: THREE.AnimationAction[] = [];
          gltf.animations.forEach((clip: THREE.AnimationClip) => {
            const action = animationMixer.clipAction(clip);

            // Set loop and clamp settings
            if (onlyInAnimation) {
              if (type === 'main') {
                // Yoga main poses: loop during hold time
                action.setLoop(THREE.LoopRepeat, Infinity);
                action.clampWhenFinished = false;
              } else {
                // Yoga in/out: play once
                action.setLoop(THREE.LoopOnce, 1);
                action.clampWhenFinished = true;
              }
            } else {
              // Normal page load: play once
              action.setLoop(THREE.LoopOnce, 1);
              action.clampWhenFinished = true;
            }

            action.play();
            maxDuration = Math.max(maxDuration, clip.duration);
            playedActions.push(action);
          });

          if (type === 'out' && playedActions.length > 0) {
            let remainingActions = playedActions.length;
            const playedActionSet = new Set(playedActions);
            const handleFinished = (event: { action?: THREE.AnimationAction }) => {
              if (!event.action || !playedActionSet.has(event.action)) {
                return;
              }
              remainingActions -= 1;
              if (remainingActions <= 0) {
                animationMixer.removeEventListener('finished', handleFinished as never);
                animationFinishedCleanupRef.current = null;
                if (animationMixer) {
                  animationMixer.stopAllAction();
                }
                onSessionEnd?.();
              }
            };

            animationMixer.addEventListener('finished', handleFinished as never);
            animationFinishedCleanupRef.current = () => {
              animationMixer.removeEventListener('finished', handleFinished as never);
            };
          }

          // IN animation plays once at its natural duration; when all clips finish,
          // transition to MAIN. No fixed-time setTimeout is used so the handoff is tight
          // regardless of the clip's actual length.
          if (type === 'in' && onlyInAnimation && playedActions.length > 0) {
            let remainingIn = playedActions.length;
            const inActionSet = new Set(playedActions);
            const handleInFinished = (event: { action?: THREE.AnimationAction }) => {
              if (!event.action || !inActionSet.has(event.action)) {
                return;
              }
              remainingIn -= 1;
              if (remainingIn <= 0) {
                animationMixer.removeEventListener('finished', handleInFinished as never);
                animationFinishedCleanupRef.current = null;
                onPhaseChange?.('main');
                playAnimationSequence(pose, 'main');
              }
            };
            animationMixer.addEventListener('finished', handleInFinished as never);
            animationFinishedCleanupRef.current = () => {
              animationMixer.removeEventListener('finished', handleInFinished as never);
            };
          }



          // Handle transitions based on spec timing

          if (onlyInAnimation) {

            // Yoga session - handle transitions like normal yoga mode
            // TODO: Re-enable warm-up/cooldown logic later
            /*
              const isWarmUpOrCooldown = playAnimationPath && (
                playAnimationPath.includes('/warm-up/') || 
                playAnimationPath.includes('/cool-down/')
              );
              
              // Don't transition for warm-up/cooldown - let them loop
              if (isWarmUpOrCooldown) {
                console.log('Warm-up/cooldown animation - no transitions, let it loop');
                return;
              }
            */



            const spec = POSE_SPEC[selectedPose || 'Mountain Pose'];

            if (spec) {

              if (type === 'main') {
                // During guided yoga sessions, the page-level hold timer controls when we
                // leave MAIN and enter the release phase. Do not auto-transition to OUT
                // here, otherwise release/out can run twice.
                if (!(onlyInAnimation && !onlyOutAnimation)) {
                  // Use spec duration for 'Hold'
                  animationTimeoutRef.current = setTimeout(() => {
                    // Notify parent that we're transitioning to OUT phase
                    onPhaseChange?.('out');

                    playAnimationSequence(pose, 'out');

                  }, spec.hold * 1000);
                }

              }
              // 'in' completion is driven by mixer 'finished' event above.
              // 'out' completion is driven by mixer 'finished' event above.

            }

          } else {

            // Normal page load - no transitions, just play in animation once and stop

          }

        } else {

          console.warn(`No animations found in ${type} GLB file`);

        }



        loadedModel.traverse((child: THREE.Object3D) => {

          if (child instanceof THREE.Mesh) {

            child.castShadow = true;

            child.receiveShadow = true;



            // Ensure material is properly set

            if (child.material) {

              child.material.needsUpdate = true;

              // Add some color if material is basic

              if (!child.material.color) {

                child.material.color = new THREE.Color(0xffffff);

              }

            }

          }

        });



        loadedModel.scale.set(1.2, 1.2, 1.2);

        loadedModel.position.set(0, -1, 0);



        setModel(loadedModel);

        findJawBone(loadedModel);

        // Notify parent of the loaded model for camera fitting
        onModelLoaded?.(loadedModel);

        // Dispose the previous phase's GPU + image-pixel memory now that React has
        // a new model to swap in. Deferred one macrotask so the scene-graph swap
        // commits before we free the old resources.
        if (previousModel && previousModel !== loadedModel && !(previousModel as any).__isSharedClone) {
          setTimeout(() => {
            try { disposeObject3D(previousModel); } catch { }
          }, 0);
        }

        // Clear loading state after model is set
        onLoadingChange?.(false);

        setCurrentAnimation(type);

        // Notify parent of phase change
        onPhaseChange?.(type);

        console.log(`Successfully loaded ${type} animation for ${selectedPose}`);

      } catch (error) {

        onLoadingChange?.(false);
        console.error(`Error loading ${type} animation:`, error);

      }

    }



    return () => {

      if (animationTimeoutRef.current) {

        clearTimeout(animationTimeoutRef.current);

      }

    };

  }, [selectedPose, staticMode, staticModelPath, playAnimationKey, onlyInAnimation, onlyOutAnimation]);



  useEffect(() => {

    if (!staticMode || playAnimationKey === undefined || playAnimationKey === 0 || !playAnimationPath) {

      return;

    }



    let isCancelled = false;



    const playAnimation = async () => {

      try {
        // TODO: Re-enable warm-up/cooldown logic later
        /*
          const isWarmUpOrCooldown = playAnimationPath && (
            playAnimationPath.includes('/warm-up/') ||
            playAnimationPath.includes('/cool-down/')
          );
        */
        const isWarmUpOrCooldown = false; // Temporarily disabled

        const shouldReuseStaticChessModel =
          !!meshRef.current &&
          !!staticModelPath &&
          playAnimationPath === staticModelPath;

        if (
          shouldReuseStaticChessModel &&
          !isWarmUpOrCooldown &&
          cachedChessClipsRef.current &&
          cachedChessClipsRef.current.length > 0
        ) {
          console.log('🎬 Playing chess animation from cache:', playAnimationPath);

          if (mixer) {
            mixer.stopAllAction();
          }

          const animationRoot = meshRef.current!;
          const animationMixer = new THREE.AnimationMixer(animationRoot);
          setMixer(animationMixer);

          cachedChessClipsRef.current.forEach((clip: THREE.AnimationClip) => {
            const action = animationMixer.clipAction(clip);
            action.reset();
            action.setLoop(THREE.LoopOnce, 1);
            action.clampWhenFinished = true;
            action.fadeIn(0.15);
            action.play();
          });

          return;
        }

        // TODO: Re-enable warm-up/cooldown logic later
        /*
          if (isWarmUpOrCooldown) {
            console.log(' Playing warm-up/cooldown animation:', playAnimationPath);
          } else {
            console.log(' Playing yoga pose animation:', playAnimationPath);
          }
        */
        console.log(' Playing yoga pose animation:', playAnimationPath);


        const loader = new GLTFLoader();



        if (dracoLoaderRef.current) loader.setDRACOLoader(dracoLoaderRef.current);
        if (ktx2LoaderRef.current) loader.setKTX2Loader(ktx2LoaderRef.current);



        const gltf = await loader.loadAsync(playAnimationPath);

        if (isCancelled) {

          return;

        }



        const loadedModel = gltf.scene;

        const shouldReuseLoadedModelAsAnimationRoot =
          !!meshRef.current &&
          !!staticModelPath &&
          playAnimationPath === staticModelPath;

        const animationRoot: THREE.Object3D = shouldReuseLoadedModelAsAnimationRoot
          ? meshRef.current!
          : loadedModel;

        if (mixer) {
          mixer.stopAllAction();
          mixer.uncacheRoot(animationRoot);
        }

        const animationMixer = new THREE.AnimationMixer(animationRoot);

        setMixer(animationMixer);



        let maxDuration = 0;

        if (gltf.animations && gltf.animations.length > 0) {

          console.log(' Found animations:', gltf.animations.map(a => a.name));

          gltf.animations.forEach((clip: THREE.AnimationClip) => {
            const action = animationMixer.clipAction(clip);

            // TODO: Re-enable warm-up/cooldown logic later
            /*
              if (isWarmUpOrCooldown) {
                // Warm-up/cooldown: always loop
                action.setLoop(THREE.LoopRepeat, Infinity);
                action.clampWhenFinished = false;
                console.log(' Warm-up/cooldown animation set to loop');
              } else {
                // Chess animations: play once
                action.setLoop(THREE.LoopOnce, 1);
                action.clampWhenFinished = true;
              }
            */
            // Chess animations: play once
            action.setLoop(THREE.LoopOnce, 1);
            action.clampWhenFinished = true;

            action.play();
            maxDuration = Math.max(maxDuration, clip.duration);
          });

        } else {

          console.warn('No animations found in model');

        }

        if (!shouldReuseLoadedModelAsAnimationRoot) {
          if (meshRef.current) {
            scene.remove(meshRef.current);
          }

          loadedModel.position.set(0, -1, 0);
          loadedModel.scale.setScalar(1.2);
          scene.add(loadedModel);
          meshRef.current = loadedModel;
          setModel(loadedModel);
        }
        onModelLoaded?.(animationRoot);

        // Detect blendshapes for TTS animation (for chess models) - PRIORITIZE main body mesh
        let mainBodyMeshFound = false;
        animationRoot.traverse((child: THREE.Object3D) => {
          if (child instanceof THREE.Mesh && child.morphTargetInfluences && child.morphTargetInfluences.length > 0) {
            // Prioritize meshes with jawOpen/mouthClose AND most blendshapes (main body mesh)
            const hasMainFaceBlendshapes = child.morphTargetDictionary && (
              Object.keys(child.morphTargetDictionary).some(name =>
                name.toLowerCase().includes('jawopen') ||
                name.toLowerCase().includes('mouthopen') ||
                name.toLowerCase().includes('mouthclose')
              )
            );

            // Only set as main blendshape mesh if it has face blendshapes AND more blendshapes than current
            if ((!blendshapeMeshRef.current && hasMainFaceBlendshapes) ||
              (hasMainFaceBlendshapes && child.morphTargetInfluences && child.morphTargetInfluences.length > (blendshapeMeshRef.current?.morphTargetInfluences?.length || 0))) {
              blendshapeMeshRef.current = child;
              blendshapeNamesRef.current = child.morphTargetDictionary ? Object.keys(child.morphTargetDictionary) : [];
              originalBlendshapesRef.current = [...(child.morphTargetInfluences || [])];
              // console.log('🎭 Found blendshape mesh for chess avatar:', child.name, 'with', blendshapeNamesRef.current.length, 'blendshapes', hasMainFaceBlendshapes ? '(MAIN FACE)' : '(secondary)');
              // console.log('🎭 Available blendshapes:', blendshapeNamesRef.current);
              if (hasMainFaceBlendshapes) mainBodyMeshFound = true;
            }
          }
        });

        console.log('🎭 FINAL: Using blendshape mesh:', blendshapeMeshRef.current?.name, 'with', blendshapeNamesRef.current.length, 'blendshapes');

        // Set timeout only for chess animations (not warm-up/cooldown) - DISABLED for TTS sync
        // TODO: Re-enable warm-up/cooldown logic later
        /*
          if (!isWarmUpOrCooldown && maxDuration > 0) {
            // COMPLETELY DISABLED: Don't stop animation to allow TTS sync
            console.log('🎭 Animation will continue for TTS sync');
          } else if (isWarmUpOrCooldown) {
            console.log('🔄 Warm-up/cooldown animation will loop continuously');
            // Add timeout to stop cool-down animation after session ends
            if (playAnimationPath && playAnimationPath.includes('/cool-down/')) {
              animationTimeoutRef.current = setTimeout(() => {
                if (animationMixer) {
                  animationMixer.stopAllAction();
                }
              }, 60000); // Stop after 60 seconds as fallback
            }
          }
        */
        // Chess animations: continue for TTS sync
        if (maxDuration > 0) {
          console.log('🎭 Animation will continue for TTS sync');
        }

      } catch (error) {

        console.error('Error playing animation:', error);

      }

    };



    playAnimation();



    return () => {

      isCancelled = true;

      if (animationTimeoutRef.current) {

        clearTimeout(animationTimeoutRef.current);

        animationTimeoutRef.current = null;

      }
      if (animationFinishedCleanupRef.current) {
        animationFinishedCleanupRef.current();
        animationFinishedCleanupRef.current = null;
      }

    };

  }, [playAnimationKey, playAnimationPath, staticMode]);



  // TTS blendshape animation effect

  useFrame((state, delta) => {

    const time = state.clock.elapsedTime;

    if (meshRef.current && model) {

      // Update animation mixer only if not paused

      if (mixer && !isPaused) {

        mixer.update(delta);

      }



      const assistantSpeaking = assistantSpeakingRef.current;
      const effectiveSpeaking = (isTTSSpeaking || assistantSpeaking) && !isPaused;

      // Smooth speech envelope (attack/release) so lip motion feels less robotic.
      // We use assistant audio level when available; otherwise fall back to a gentle baseline while TTS is active.
      const rawSpeechLevel = effectiveSpeaking
        ? (assistantSpeaking ? assistantAudioLevelRef.current : 0.35)
        : 0;
      const env = speechEnvelopeRef.current;
      const attack = 0.22;
      const release = 0.12;
      const k = rawSpeechLevel > env ? attack : release;
      speechEnvelopeRef.current = THREE.MathUtils.lerp(env, rawSpeechLevel, k);

      if (!didLogAssistantDriverRef.current && (assistantAudioLevelRef.current > 0.02 || assistantSpeaking)) {
        didLogAssistantDriverRef.current = true;
        console.log('[Avatar3D] assistant driver active', {
          jawBoneFound: !!jawBoneRef.current,
          blendshapeMesh: blendshapeMeshRef.current?.name || null,
          blendshapeCount: blendshapeNamesRef.current.length,
        });
      }

      if (effectiveSpeaking && jawBoneRef.current) {
        const target = Math.max(0, Math.min(0.42, speechEnvelopeRef.current * 0.7));
        const targetRot = -target * 0.18;
        jawBoneRef.current.rotation.x = THREE.MathUtils.lerp(jawBoneRef.current.rotation.x, targetRot, 0.18);
      }

      if (!effectiveSpeaking && jawBoneRef.current) {
        jawBoneRef.current.rotation.x = THREE.MathUtils.lerp(jawBoneRef.current.rotation.x, 0, 0.18);
      }

      if (effectiveSpeaking && blendshapeMeshRef.current && blendshapeMeshRef.current.morphTargetInfluences) {



        // Viseme-style gating: vary between wide / round / open shapes and add micro-pauses.
        const envLevel = Math.max(0, Math.min(1, speechEnvelopeRef.current));
        const syllable = 0.5 + 0.5 * Math.sin((time + speechSeedRef.current) * 7.2);
        const microPause = Math.pow(Math.max(0, Math.sin((time + speechSeedRef.current) * 3.1)), 12);
        const gate = THREE.MathUtils.clamp(0.25 + 0.75 * syllable - microPause * 0.55, 0, 1);

        // Jaw movement - moderate, not too extreme
        const jawAmount = 0.25 + 0.45 * gate; // 0.25 to 0.70 - visible but not exaggerated

        // Lip open - minimal, just subtle movement
        const openAmount = envLevel * (0.02 + 0.06 * gate); // Very minimal lip movement
        const wideAmount = envLevel * (0.02 + 0.06 * (0.5 + 0.5 * Math.sin((time + speechSeedRef.current) * 4.9)));
        const roundAmount = envLevel * (0.01 + 0.04 * (0.5 + 0.5 * Math.sin((time + speechSeedRef.current) * 4.1 + 1.7)));

        // Debug: Log available blendshapes once
        if (Math.floor(time * 2) % 8 === 0 && Math.floor((time - 0.01) * 2) % 8 !== 0) {
          // console.log('🎭 Available blendshapes:', blendshapeNamesRef.current.slice(0, 30));
        }

        // Directly drive key ARKit mouth targets for visible motion
        let didDriveArkitMouth = false;
        try {
          const dict = blendshapeMeshRef.current.morphTargetDictionary || {};
          const influences = blendshapeMeshRef.current.morphTargetInfluences;

          // Debug: Log what we're trying to set
          if (Math.floor(time * 3) % 6 === 0) {
            // console.log('👄 Lip-sync values:', {
            //   jawOpen: (dict as any).jawOpen,
            //   jawAmount: jawAmount.toFixed(3),
            //   mouthClose: (dict as any).mouthClose,
            //   upperUpL: (dict as any).mouthUpperUpLeft,
            //   lowerDownL: (dict as any).mouthLowerDownLeft,
            //   funnel: (dict as any).mouthFunnel,
            //   teeth: (dict as any).teeth
            // });
          }

          // Jaw open - STRONGER for visible jaw movement
          const jawIdx = (dict as any).jawOpen;
          if (typeof jawIdx === 'number') {
            didDriveArkitMouth = true;
            influences[jawIdx] = THREE.MathUtils.lerp(influences[jawIdx] || 0, jawAmount, 0.28);
          }

          // Mouth close - counteract jawOpen *only when needed*.
          // Use `gate` so vowels/open syllables can open naturally while keeping lips from over-opening.
          const closeIdx = (dict as any).mouthClose;
          if (typeof closeIdx === 'number') {
            const closeAmount = THREE.MathUtils.clamp(jawAmount * (0.65 - 0.55 * gate), 0, 0.55);
            influences[closeIdx] = THREE.MathUtils.lerp(influences[closeIdx] || 0, closeAmount, 0.22);
          }

          // Upper lip movement - MINIMAL, don't add to lip opening
          const upperUpLIdx = (dict as any).mouthUpperUpLeft;
          const upperUpRIdx = (dict as any).mouthUpperUpRight;
          const upperUpIdx = (dict as any).mouthUpperUp;
          const lipUpperIdx = (dict as any).lipUpperUp;

          // Subtle upper lip movement only
          const upperLipValue = openAmount * 0.18;
          if (typeof upperUpLIdx === 'number') influences[upperUpLIdx] = THREE.MathUtils.lerp(influences[upperUpLIdx] || 0, upperLipValue, 0.2);
          if (typeof upperUpRIdx === 'number') influences[upperUpRIdx] = THREE.MathUtils.lerp(influences[upperUpRIdx] || 0, upperLipValue, 0.2);
          if (typeof upperUpIdx === 'number') influences[upperUpIdx] = THREE.MathUtils.lerp(influences[upperUpIdx] || 0, upperLipValue, 0.2);
          if (typeof lipUpperIdx === 'number') influences[lipUpperIdx] = THREE.MathUtils.lerp(influences[lipUpperIdx] || 0, upperLipValue * 0.5, 0.2);

          // Lower lip movement - MINIMAL, synced with jaw
          const lowerDownLIdx = (dict as any).mouthLowerDownLeft;
          const lowerDownRIdx = (dict as any).mouthLowerDownRight;
          const lowerDownIdx = (dict as any).mouthLowerDown;
          const lipLowerIdx = (dict as any).lipLowerDown;

          // Subtle lower lip movement
          const lowerLipValue = jawAmount * 0.10;
          if (typeof lowerDownLIdx === 'number') influences[lowerDownLIdx] = THREE.MathUtils.lerp(influences[lowerDownLIdx] || 0, lowerLipValue, 0.22);
          if (typeof lowerDownRIdx === 'number') influences[lowerDownRIdx] = THREE.MathUtils.lerp(influences[lowerDownRIdx] || 0, lowerLipValue, 0.22);
          if (typeof lowerDownIdx === 'number') influences[lowerDownIdx] = THREE.MathUtils.lerp(influences[lowerDownIdx] || 0, lowerLipValue, 0.22);
          if (typeof lipLowerIdx === 'number') influences[lipLowerIdx] = THREE.MathUtils.lerp(influences[lipLowerIdx] || 0, lowerLipValue * 0.5, 0.22);

          // Mouth funnel and pucker for rounded sounds
          const funnelIdx = (dict as any).mouthFunnel;
          if (typeof funnelIdx === 'number')
            influences[funnelIdx] = THREE.MathUtils.lerp(
              influences[funnelIdx] || 0,
              roundAmount * (0.50 + 0.20 * (0.5 + 0.5 * Math.sin((time + speechSeedRef.current) * 2.0))),
              0.18
            );

          const puckerIdx = (dict as any).mouthPucker;
          if (typeof puckerIdx === 'number')
            influences[puckerIdx] = THREE.MathUtils.lerp(
              influences[puckerIdx] || 0,
              roundAmount * (0.45 + 0.20 * (0.5 + 0.5 * Math.sin((time + speechSeedRef.current) * 1.6 + 0.6))),
              0.18
            );

          // Smile - subtle, adds life
          const smileIdx = (dict as any).mouthSmileLeft || (dict as any).mouthSmile;
          const smileRIdx = (dict as any).mouthSmileRight;
          const smileValue = 0.03 + wideAmount * 0.5;
          if (typeof smileIdx === 'number') influences[smileIdx] = THREE.MathUtils.lerp(influences[smileIdx] || 0, smileValue, 0.12);
          if (typeof smileRIdx === 'number') influences[smileRIdx] = THREE.MathUtils.lerp(influences[smileRIdx] || 0, smileValue, 0.12);

          // Teeth visibility - SHOW when mouth opens, HIDE when closed (natural human behavior)
          const teethIdx = (dict as any).teeth || (dict as any).Teeth;
          if (typeof teethIdx === 'number') {
            // Teeth visible when jaw opens, hidden during pauses/closed
            const teethVisible = jawAmount > 0.15 ? jawAmount * 0.6 : 0;
            influences[teethIdx] = THREE.MathUtils.lerp(influences[teethIdx] || 0, teethVisible, 0.2);
          }
        } catch { }

        // Look for mouth-related blendshapes - expanded list with visemes

        const mouthBlendshapes = blendshapeNamesRef.current.filter((name) => {
          const n = name.toLowerCase();
          if (n === 'jawopen') return false;
          if (n === 'mouthclose') return false;
          if (n === 'mouthfunnel') return false;
          if (n === 'mouthpucker') return false;
          return n.includes('mouth') || n.includes('jaw') || n.includes('lip') || n.includes('tongue') || n.includes('viseme');
        });



        if (!didDriveArkitMouth && mouthBlendshapes.length > 0) {

          const chessBoost = staticMode && (staticModelPath || '').includes('Encouraging Gesture') ? 0.8 : 1.0;

          const energy = assistantSpeaking ? assistantAudioLevelRef.current : 0.35;
          const targetMouth = Math.max(0, Math.min(0.16, energy * 0.22)) * chessBoost;

          // Natural human-like animation

          mouthBlendshapes.forEach((blendshapeName, index) => {

            const morphIndex = blendshapeMeshRef.current!.morphTargetDictionary?.[blendshapeName];

            if (morphIndex !== undefined && blendshapeMeshRef.current!.morphTargetInfluences) {

              // Natural talking animation - much more subtle

              const baseValue = Math.abs(Math.sin(time * 3 + index)) * 0.12;
              const variation = Math.sin(time * 6 + index * 0.2) * 0.06;
              const finalValue = Math.min(1.0, baseValue + variation + targetMouth);



              // Special handling for key mouth blendshapes - more natural values

              if (blendshapeName.toLowerCase().includes('jawopen') ||

                blendshapeName.toLowerCase().includes('mouthopen')) {

                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = Math.min(1, finalValue * 0.95); // Stronger jaw opening

              } else if (blendshapeName.toLowerCase().includes('mouthclose')) {

                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = Math.min(1, finalValue * 0.35); // Stronger closing

              } else if (blendshapeName.toLowerCase().includes('tongueout')) {

                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = Math.min(1, finalValue * 0.55); // Stronger tongue movement

              } else if (blendshapeName.toLowerCase().includes('viseme')) {
                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = Math.min(1, finalValue * 0.8); // Stronger viseme animation
              } else {
                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = Math.min(1, finalValue * 0.7); // Stronger mouth movement
              }

            }

          });

          // Debug log occasionally - show all available blendshapes

          if (Math.floor(time * 2) % 4 === 0) {

            // console.log('All available blendshapes:', blendshapeNamesRef.current.slice(0, 20));

            // console.log('Animating blendshapes:', mouthBlendshapes.slice(0, 5));



            // Show actual morph target values for debugging

            mouthBlendshapes.forEach((blendshapeName, index) => {

              const morphIndex = blendshapeMeshRef.current!.morphTargetDictionary?.[blendshapeName];

              if (morphIndex !== undefined && blendshapeMeshRef.current!.morphTargetInfluences) {

                const value = blendshapeMeshRef.current!.morphTargetInfluences[morphIndex];

                // console.log(`${blendshapeName}: ${value.toFixed(3)}`);

              }

            });

          }

        } else {

          // Fallback: try to animate any available blendshapes

          const availableBlendshapes = blendshapeNamesRef.current.slice(0, 3);

          availableBlendshapes.forEach((blendshapeName, index) => {

            const morphIndex = blendshapeMeshRef.current!.morphTargetDictionary?.[blendshapeName];

            if (morphIndex !== undefined && blendshapeMeshRef.current!.morphTargetInfluences) {

              const value = Math.abs(Math.sin(time * 6 + index)) * 0.2;

              blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = value;

            }

          });



          if (Math.floor(time * 2) % 4 === 0) {

            // console.log('Fallback blendshape animation, using:', availableBlendshapes);

          }

        }

        const blinkBlendshapes = blendshapeNamesRef.current.filter((name) => {
          const n = name.toLowerCase();
          return n.includes('blink') || n.includes('eyelid') || n.includes('eyeclose');
        });

        if (blinkBlendshapes.length > 0) {
          blinkPhaseRef.current += delta;
          const blinkEvery = assistantSpeaking ? 2.4 : 4.2;
          if (blinkPhaseRef.current > blinkEvery) {
            blinkPhaseRef.current = 0;
          }
          const blinkT = blinkPhaseRef.current;
          const blinkAmt = blinkT < 0.12 ? (blinkT / 0.12) : blinkT < 0.22 ? (1 - (blinkT - 0.12) / 0.1) : 0;
          blinkBlendshapes.forEach((blendshapeName) => {
            const morphIndex = blendshapeMeshRef.current!.morphTargetDictionary?.[blendshapeName];
            if (morphIndex !== undefined && blendshapeMeshRef.current!.morphTargetInfluences) {
              const cur = blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] || 0;
              blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = THREE.MathUtils.lerp(cur, blinkAmt, 0.35);
            }
          });
        }

      } else if (!effectiveSpeaking && blendshapeMeshRef.current && blendshapeMeshRef.current.morphTargetInfluences) {

        // Return to original blendshape values when not speaking

        blendshapeMeshRef.current.morphTargetInfluences.forEach((value, index) => {

          const originalValue = (originalBlendshapesRef.current && originalBlendshapesRef.current[index]) || 0;

          if (blendshapeMeshRef.current && blendshapeMeshRef.current.morphTargetInfluences) {

            blendshapeMeshRef.current.morphTargetInfluences[index] = THREE.MathUtils.lerp(value, originalValue, 0.1);

          }

        });

      }

      // Keep subtle forward lean so the avatar still feels alive while speaking.
      if (meshRef.current) {
        const baseForwardLeanX = 0.22;
        const bobX = effectiveSpeaking ? Math.sin(time * 2.2) * 0.02 : 0;
        const targetX = baseForwardLeanX + bobX;
        meshRef.current.rotation.x = THREE.MathUtils.lerp(meshRef.current.rotation.x, targetX, 0.08);
      }



      // Smooth rotation to target angle

      const spec = POSE_SPEC[selectedPose || 'Mountain Pose'];

      if (spec && !disablePoseMotion) {
        // TODO: Re-enable warm-up/cooldown logic later
        /*
          const isWarmUpOrCooldown = playAnimationPath && (
            playAnimationPath.includes('/warm-up/') ||
            playAnimationPath.includes('/cool-down/')
          );
        */
        const isWarmUpOrCooldown = false; // Temporarily disabled

        // Don't change angles during warmup/cooldown
        if (!isWarmUpOrCooldown) {

          // Spec: 90=Front, 180=Right Profile, 270=Back, 360=Left Profile

          let targetAngle = spec.angle;

          if (currentAnimation === 'main') {
            // Keep whatever angle was reached at the end of previous phase
            // If coming from 'out', use opposite angle for anticlockwise movement
            const currentAngleDeg = (meshRef.current.rotation.y * 180) / Math.PI + 90;
            targetAngle = currentAngleDeg;
          } else if (currentAnimation === 'out') {
            // OUT should end on front (90deg). Rotate smoothly and clamp at target.
            // For cases like 180 -> 90, force anticlockwise (decreasing degrees).
            const currentAngleDegRaw = (meshRef.current.rotation.y * 180) / Math.PI + 90;
            const currentAngleDeg = ((currentAngleDegRaw % 360) + 360) % 360;

            const targetAngleOut = 90;
            const targetRadOut = (targetAngleOut - 90) * (Math.PI / 180); // 0
            const currentRadOut = meshRef.current.rotation.y;

            let diffOut = targetRadOut - currentRadOut;
            // If the model is on the right/back side (> 90deg), force anticlockwise by taking the long path.
            if (currentAngleDeg > 90 && diffOut > 0) {
              diffOut -= 2 * Math.PI;
            }

            const maxStepOut = (15 * Math.PI / 180) * delta;

            // Clamp to avoid overshoot: if we're within one step, snap exactly to target.
            if (Math.abs(diffOut) <= maxStepOut) {
              meshRef.current.rotation.y = targetRadOut;
            } else {
              meshRef.current.rotation.y += Math.sign(diffOut) * maxStepOut;
            }

            return;
          } else {
            // 'in' (and any other state) uses pose's defined angle
            targetAngle = spec.angle;
          }

          const targetRad = (targetAngle - 90) * (Math.PI / 180);

          // Max rotation speed: 10-15 deg/s
          const maxStep = (15 * Math.PI / 180) * delta;

          // Smoothly rotate

          const diff = targetRad - meshRef.current.rotation.y;

          if (Math.abs(diff) > 0.001) {

            meshRef.current.rotation.y += Math.sign(diff) * Math.min(Math.abs(diff), maxStep);

          }

        }

      } else {

        // Default subtle idle rotation if no spec

        meshRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.05;

      }

    }

  });



  if (!model) {

    return null;

  }



  return <primitive ref={meshRef} object={model} />;

}



interface Avatar3DProps {

  selectedPose?: string;

  onlyInAnimation?: boolean; // New prop for onboarding page

  disablePoseMotion?: boolean;

  isTTSSpeaking?: boolean; // New prop for TTS sync

  isPaused?: boolean; // New prop for pause/resume

  staticMode?: boolean; // New prop for static avatar without animation

  staticModelPath?: string; // Optional custom static model (e.g. chess)

  playAnimationPath?: string; // Optional custom animation model (e.g. chess)

  playAnimationKey?: number; // Increment to trigger one-shot animation

  cameraZoom?: number;

  cameraPositionYRaise?: number;

  cameraDistanceScale?: number;

  cameraManualDistanceFactor?: number;

  cameraManualTargetYOffsetFactor?: number;

  cameraManualTargetXOffsetFactor?: number;

  lockCamera?: boolean;

  skinToneColor?: string;

  skinToneStrength?: number;

  onSessionEnd?: () => void; // Callback when OUT animation completes

  onModelLoaded?: (model: THREE.Object3D | null) => void;

}



export default function Avatar3D({ selectedPose = "Mountain Pose", onlyInAnimation = false, onlyOutAnimation = false, disablePoseMotion = false, isTTSSpeaking = false, isPaused = false, staticMode = false, staticModelPath, playAnimationPath, playAnimationKey, cameraZoom = 1, cameraTargetYOffset = 0, cameraPositionYRaise = 0, cameraDistanceScale = 1, cameraManualDistanceFactor, cameraManualTargetYOffsetFactor, cameraManualTargetXOffsetFactor, lockCamera = false, skinToneColor = '#d9a07f', skinToneStrength = 0.28, onTTSSpeaking, onError, onSessionEnd, onPhaseChange }: Avatar3DProps) {

  const [webglSupported, setWebglSupported] = useState(true);

  const [error, setError] = useState<string | null>(null);

  const [modelLoading, setModelLoading] = useState(true);

  const [fitObject, setFitObject] = useState<THREE.Object3D | null>(null);
  const [cameraTarget, setCameraTarget] = useState<[number, number, number]>([0, 0, 0]);
  const [fitTick, setFitTick] = useState(0);
  const [referenceSize, setReferenceSize] = useState<THREE.Vector3 | null>(
    lockCamera ? YOGA_REFERENCE_SIZE.clone() : null
  );
  // When lockCamera is true (yoga session/instructions), seed with the universal yoga
  // bounding box so the camera distance is consistent regardless of each pose's
  // IN-animation first-frame size.
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const fitRefreshRafRef = useRef<number | null>(null);

  const scheduleFitRefresh = useCallback(() => {
    if (typeof window === 'undefined') return;

    if (fitRefreshRafRef.current !== null) {
      window.cancelAnimationFrame(fitRefreshRafRef.current);
      fitRefreshRafRef.current = null;
    }

    fitRefreshRafRef.current = window.requestAnimationFrame(() => {
      fitRefreshRafRef.current = window.requestAnimationFrame(() => {
        setFitTick((prev) => prev + 1);
        fitRefreshRafRef.current = null;
      });
    });
  }, []);

  const handleModelLoaded = useCallback((model: THREE.Object3D | null) => {
    setFitObject(model);
    if (model) {
      try {
        const box = new THREE.Box3().setFromObject(model);
        const nextSize = new THREE.Vector3();
        box.getSize(nextSize);
        setReferenceSize((prev) => {
          if (!prev) {
            return nextSize.clone();
          }

          const merged = new THREE.Vector3(
            Math.max(prev.x, nextSize.x),
            Math.max(prev.y, nextSize.y),
            Math.max(prev.z, nextSize.z)
          );

          const changed =
            Math.abs(merged.x - prev.x) > 0.001 ||
            Math.abs(merged.y - prev.y) > 0.001 ||
            Math.abs(merged.z - prev.z) > 0.001;

          return changed ? merged : prev;
        });
      } catch { }
    }
    scheduleFitRefresh();
  }, [scheduleFitRefresh]);

  useEffect(() => {
    if (!modelLoading && fitObject) {
      scheduleFitRefresh();
    }
  }, [modelLoading, fitObject, scheduleFitRefresh]);

  // Free the WebGL context on unmount. Without this, each Avatar3D remount
  // (flowStage change, pose restart) leaves a live GL context holding GPU memory
  // until the browser eventually recycles it.
  useEffect(() => {
    return () => {
      if (fitRefreshRafRef.current !== null) {
        try { window.cancelAnimationFrame(fitRefreshRafRef.current); } catch { }
        fitRefreshRafRef.current = null;
      }
      const gl = rendererRef.current;
      if (gl) {
        try { gl.renderLists?.dispose?.(); } catch { }
        try { gl.dispose?.(); } catch { }
      }
      rendererRef.current = null;
    };
  }, []);



  useEffect(() => {

    // Check WebGL support

    const canvas = document.createElement('canvas');

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) {
      setWebglSupported(false);
      setError('WebGL is not supported in this browser');
    }
  }, []);

  // Always show a fallback for walktour purposes
  return (
    <div className="w-full h-full flex items-end justify-center" style={{ position: "relative" }} data-walktour="avatar">
      {webglSupported && !error ? (
        <div className="w-full h-full flex items-end justify-center" style={{ position: "relative" }}>
          {modelLoading && (
            <div style={{
              position: 'absolute',
              inset: 0,
              zIndex: 10,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none',
            }}>
              <div style={{
                width: 40,
                height: 40,
                border: '3px solid rgba(255,255,255,0.15)',
                borderTopColor: 'rgba(255,255,255,0.7)',
                borderRadius: '50%',
                animation: 'avatar-spin 0.8s linear infinite',
              }} />
              <style>{`@keyframes avatar-spin { to { transform: rotate(360deg); } }`}</style>
            </div>
          )}
          <Canvas
            camera={{ position: [0, 0, 3], fov: 50 }}
            dpr={[1, 1.5]}
            gl={{
              antialias: true,
              alpha: true,
              powerPreference: "high-performance",
              failIfMajorPerformanceCaveat: false
            }}
            onCreated={({ gl }) => {
              rendererRef.current = gl;
            }}
            style={{
              background: "transparent",
              width: "100%",
              height: "100%",
              opacity: modelLoading ? 0 : 1,
              transition: "opacity 0.3s ease-in",
            }}
          >
            <ambientLight intensity={0.6} />
            <directionalLight
              position={[5, 5, 5]}
              intensity={1}
              castShadow
              shadow-mapSize-width={512}
              shadow-mapSize-height={512}
            />
            <directionalLight position={[-5, 5, 5]} intensity={0.8} />
            <pointLight position={[0, 2, 2]} intensity={0.6} />
            <hemisphereLight args={[0xffffff, 0x444444, 0.3]} />
            <AutoFitCamera object={fitObject} referenceSize={referenceSize} cameraZoom={cameraZoom} cameraTargetYOffset={cameraTargetYOffset} cameraPositionYRaise={cameraPositionYRaise} cameraDistanceScale={cameraDistanceScale} cameraManualDistanceFactor={cameraManualDistanceFactor} cameraManualTargetYOffsetFactor={cameraManualTargetYOffsetFactor} cameraManualTargetXOffsetFactor={cameraManualTargetXOffsetFactor} lockCamera={lockCamera} fitTick={fitTick} onTargetChange={setCameraTarget} />
            <CameraControls target={cameraTarget} />
            <Suspense fallback={null}>
              <YogaModel
                selectedPose={selectedPose}
                onlyInAnimation={onlyInAnimation}
                onlyOutAnimation={onlyOutAnimation}
                disablePoseMotion={disablePoseMotion}
                isTTSSpeaking={isTTSSpeaking}
                isPaused={isPaused}
                staticMode={staticMode}
                staticModelPath={staticModelPath}
                playAnimationPath={playAnimationPath}
                playAnimationKey={playAnimationKey}
                skinToneColor={skinToneColor}
                skinToneStrength={skinToneStrength}
                onError={setError}
                onTTSSpeaking={onTTSSpeaking}
                onModelLoaded={handleModelLoaded}
                onSessionEnd={onSessionEnd}
                onPhaseChange={onPhaseChange}
                onLoadingChange={setModelLoading}
              />
            </Suspense>
          </Canvas>
        </div>
      ) : (
        <>
          {/* Fallback image when WebGL fails */}
          <img
            src="https://images.unsplash.com/photo-1600369671668-3b0ae9f5a832?q=80&w=900&auto=format&fit=crop"
            alt="Avatar"
            className="absolute inset-0 h-full w-full object-contain p-6"
            onError={(e) => {
              console.log('Image failed to load, showing placeholder');
              e.currentTarget.style.display = 'none';
            }}
          />
          {/* Fallback placeholder */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-6xl mb-4">🧘‍♂️</div>
              <div className="text-white text-lg">AI Avatar</div>
              <div className="text-gray-400 text-sm mt-2">
                {error || '3D Avatar Loading...'}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ...
