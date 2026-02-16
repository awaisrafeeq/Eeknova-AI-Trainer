"use client";

import React, { useEffect, useState, useRef, Suspense, useCallback } from "react";

import { Canvas, useFrame, useThree } from "@react-three/fiber";

import * as THREE from "three"

import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import { DRACOLoader } from "three/examples/jsm/loaders/DRACOLoader.js";

import { KTX2Loader } from "three/examples/jsm/loaders/KTX2Loader.js";



function CameraControls() {

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



    return () => controls.current?.dispose();

  }, [camera, gl]);



  useFrame(() => controls.current?.update());

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

    inPath: "/Warrior 1 Pose/in_compressed.glb",

    mainPath: "/Warrior 1 Pose/main_compressed.glb",

    outPath: "/Warrior 1 Pose/out_compressed.glb",

  },

};



interface Avatar3DProps {
  selectedPose?: string;
  onlyInAnimation?: boolean;
  isTTSSpeaking?: boolean;
  isPaused?: boolean;
  staticMode?: boolean;
  staticModelPath?: string;
  playAnimationPath?: string;
  playAnimationKey?: number;
  onTTSSpeaking?: (speaking: boolean) => void;
  onError?: (error: string) => void;
  onSessionEnd?: () => void;
  assistantModeActive?: boolean;
}

function YogaModel({ selectedPose, onlyInAnimation = false, isTTSSpeaking = false, isPaused = false, staticMode = false, staticModelPath, playAnimationPath, playAnimationKey, onError, onTTSSpeaking, onSessionEnd }: Avatar3DProps) {

  const [model, setModel] = useState<THREE.Group | null>(null);

  const [mixer, setMixer] = useState<THREE.AnimationMixer | null>(null);

  const [currentAnimation, setCurrentAnimation] = useState<'in' | 'main' | 'out'>('in');

  const meshRef = useRef<THREE.Group>(null);

  const animationTimeoutRef = useRef<NodeJS.Timeout | null>(null);

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
        } catch {}
      }
      ktx2LoaderRef.current = null;

      if (dracoLoaderRef.current) {
        try {
          dracoLoaderRef.current.dispose();
        } catch {}
      }
      dracoLoaderRef.current = null;
    };
  }, [gl]);

  useEffect(() => {
    const onAssistantAudio = (ev: Event) => {
      try {
        const detail = (ev as CustomEvent).detail as any;
        if (!detail) return;
        const lvl = typeof detail.level === 'number' ? detail.level : 0;
        assistantAudioLevelRef.current = Math.max(0, Math.min(1, lvl));
        assistantSpeakingRef.current = !!detail.isSpeaking;
      } catch {}
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
    } catch {}
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

      const loader = new GLTFLoader();

      

      // Set up shared DRACO/KTX2 loaders (avoid repeated loader creation)
      if (dracoLoaderRef.current) loader.setDRACOLoader(dracoLoaderRef.current);
      if (ktx2LoaderRef.current) loader.setKTX2Loader(ktx2LoaderRef.current);



      console.log('Loading static avatar...');

      

      // Load yoga avatar as static model (use in animation)

      const gltf = await loader.loadAsync(modelPath || 'smile & greet_compressed.glb');

      const loadedModel = gltf.scene;



      // Set shadows and materials

      loadedModel.traverse((child) => {

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

          console.log('🎭 Found animations:', gltf.animations.map(a => a.name));

          

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

      console.error('Error loading static avatar:', error);

      onError?.('Failed to load static avatar');

    }

  };



  useEffect(() => {

    // If static mode or staticModelPath is provided, load static model

    if (staticMode || staticModelPath) {

      loadChessAvatar(staticModelPath);

      return;

    }



    // Clear any existing timeout

    if (animationTimeoutRef.current) {

      clearTimeout(animationTimeoutRef.current);

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

      loadedModel.traverse((child) => {

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

        console.error('Error loading static avatar:', error);

      }

    }



    async function playAnimationSequence(pose: PoseAnimation, type: 'in' | 'main' | 'out') {

      try {

        // Preserve current rotation across in/main/out model swaps
        const previousRotationY = meshRef.current?.rotation.y ?? 0;



        const gltf = await new Promise<any>((resolve, reject) => {

          const path = type === 'in' ? pose.inPath : type === 'main' ? pose.mainPath : pose.outPath;

          loader.load(path, resolve, undefined, reject);

        });



        const loadedModel = gltf.scene;

        // Apply previous rotation immediately so we don't snap back to front-facing (90deg)
        loadedModel.rotation.y = previousRotationY;

        if (!cachedChessClipsRef.current && gltf.animations && gltf.animations.length > 0) {
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
          });



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

              if (type === 'in') {

                // Use spec duration for 'In' 

                animationTimeoutRef.current = setTimeout(() => {

                  playAnimationSequence(pose, 'main');

                }, spec.in * 1000);

              } else if (type === 'main') {

                // Use spec duration for 'Hold'

                animationTimeoutRef.current = setTimeout(() => {

                  playAnimationSequence(pose, 'out');

                }, spec.hold * 1000);

              } else if (type === 'out') {

                // Stay on 'Out' for its duration

                animationTimeoutRef.current = setTimeout(() => {

                  // Stop the looping animation

                  if (animationMixer) {

                    animationMixer.stopAllAction();

                  }

                  // Notify parent that session ended
                  if (onSessionEnd) {
                    onSessionEnd();
                  }

                }, spec.out * 1000);

              }

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

        setCurrentAnimation(type);

        console.log(`Successfully loaded ${type} animation for ${selectedPose}`);

      } catch (error) {

        console.error(`Error loading ${type} animation:`, error);

      }

    }



    return () => {

      if (animationTimeoutRef.current) {

        clearTimeout(animationTimeoutRef.current);

      }

    };

  }, [selectedPose, staticMode, staticModelPath]);



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
              console.log('🎭 Found blendshape mesh for chess avatar:', child.name, 'with', blendshapeNamesRef.current.length, 'blendshapes', hasMainFaceBlendshapes ? '(MAIN FACE)' : '(secondary)');
              console.log('🎭 Available blendshapes:', blendshapeNamesRef.current);
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

    };

  }, [playAnimationKey, playAnimationPath, staticMode]);



  // TTS blendshape animation effect

  useFrame((state, delta) => {

    if (meshRef.current && model) {

      // Update animation mixer only if not paused

      if (mixer && !isPaused) {

        mixer.update(delta);

      }



      const assistantSpeaking = assistantSpeakingRef.current;
      const effectiveSpeaking = (isTTSSpeaking || assistantSpeaking) && !isPaused;

      if (!didLogAssistantDriverRef.current && (assistantAudioLevelRef.current > 0.02 || assistantSpeaking)) {
        didLogAssistantDriverRef.current = true;
        console.log('[Avatar3D] assistant driver active', {
          jawBoneFound: !!jawBoneRef.current,
          blendshapeMesh: blendshapeMeshRef.current?.name || null,
          blendshapeCount: blendshapeNamesRef.current.length,
        });
      }

      if (effectiveSpeaking && jawBoneRef.current) {
        const energy = assistantSpeaking ? assistantAudioLevelRef.current : 0.35;
        const target = Math.max(0, Math.min(0.42, energy * 0.55));
        const targetRot = -target * 0.18;
        jawBoneRef.current.rotation.x = THREE.MathUtils.lerp(jawBoneRef.current.rotation.x, targetRot, 0.18);
      }

      if (!effectiveSpeaking && jawBoneRef.current) {
        jawBoneRef.current.rotation.x = THREE.MathUtils.lerp(jawBoneRef.current.rotation.x, 0, 0.18);
      }

      if (effectiveSpeaking && blendshapeMeshRef.current && blendshapeMeshRef.current.morphTargetInfluences) {

        const time = state.clock.elapsedTime;

        

        // Directly drive key ARKit mouth targets for visible motion
        try {
          const dict = blendshapeMeshRef.current.morphTargetDictionary || {};
          const influences = blendshapeMeshRef.current.morphTargetInfluences;
          const energy = assistantSpeaking ? assistantAudioLevelRef.current : 0.35;
          const target = Math.max(0, Math.min(0.28, energy * 0.35));
          const jawIdx = (dict as any).jawOpen;
          if (typeof jawIdx === 'number') influences[jawIdx] = THREE.MathUtils.lerp(influences[jawIdx] || 0, target, 0.22);

          const closeIdx = (dict as any).mouthClose;
          if (typeof closeIdx === 'number') influences[closeIdx] = THREE.MathUtils.lerp(influences[closeIdx] || 0, Math.max(0, 0.22 - target), 0.22);

          const funnelIdx = (dict as any).mouthFunnel;
          if (typeof funnelIdx === 'number')
            influences[funnelIdx] = THREE.MathUtils.lerp(
              influences[funnelIdx] || 0,
              target * (0.18 + 0.08 * Math.abs(Math.sin(time * 2.4))),
              0.16
            );

          const puckerIdx = (dict as any).mouthPucker;
          if (typeof puckerIdx === 'number')
            influences[puckerIdx] = THREE.MathUtils.lerp(
              influences[puckerIdx] || 0,
              target * (0.14 + 0.06 * Math.abs(Math.sin(time * 1.7))),
              0.16
            );
        } catch {}

        // Look for mouth-related blendshapes - expanded list with visemes

        const mouthBlendshapes = blendshapeNamesRef.current.filter((name) => {
          const n = name.toLowerCase();
          if (n === 'jawopen') return false;
          if (n === 'mouthclose') return false;
          if (n === 'mouthfunnel') return false;
          if (n === 'mouthpucker') return false;
          return n.includes('mouth') || n.includes('jaw') || n.includes('lip') || n.includes('tongue') || n.includes('viseme');
        });

        

        if (mouthBlendshapes.length > 0) {

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

        if (meshRef.current) {
          const targetX = assistantSpeaking ? Math.sin(time * 2.2) * 0.02 : 0;
          meshRef.current.rotation.x = THREE.MathUtils.lerp(meshRef.current.rotation.x, targetX, 0.08);
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

      if (!effectiveSpeaking && meshRef.current) {
        meshRef.current.rotation.x = THREE.MathUtils.lerp(meshRef.current.rotation.x, 0, 0.08);
      }



      // Smooth rotation to target angle

      const spec = POSE_SPEC[selectedPose || 'Mountain Pose'];

      if (spec) {
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

    return (

      <mesh>

        <boxGeometry args={[1, 2, 0.5]} />

        <meshStandardMaterial color="#00ffff" wireframe />

      </mesh>

    );

  }



  return <primitive ref={meshRef} object={model} />;

}



interface Avatar3DProps {

  selectedPose?: string;

  onlyInAnimation?: boolean; // New prop for onboarding page

  isTTSSpeaking?: boolean; // New prop for TTS sync

  isPaused?: boolean; // New prop for pause/resume

  staticMode?: boolean; // New prop for static avatar without animation

  staticModelPath?: string; // Optional custom static model (e.g. chess)

  playAnimationPath?: string; // Optional custom animation model (e.g. chess)

  playAnimationKey?: number; // Increment to trigger one-shot animation

  onSessionEnd?: () => void; // Callback when OUT animation completes

}



export default function Avatar3D({ selectedPose = "Mountain Pose", onlyInAnimation = false, isTTSSpeaking = false, isPaused = false, staticMode = false, staticModelPath, playAnimationPath, playAnimationKey, onTTSSpeaking, onError, onSessionEnd }: Avatar3DProps) {

  const [webglSupported, setWebglSupported] = useState(true);

  const [error, setError] = useState<string | null>(null);



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
    <div className="w-full h-full flex items-center justify-center" style={{ position: "relative" }} data-walktour="avatar">
      {webglSupported && !error ? (
        <div className="w-full h-full" style={{ position: "relative" }}>
          <Canvas
            camera={{ position: [0, 0, 3], fov: 50 }}
            gl={{
              antialias: true,
              alpha: true,
              powerPreference: "high-performance",
              failIfMajorPerformanceCaveat: false
            }}
            style={{ background: "transparent", width: "100%", height: "100%" }}
          >
            <ambientLight intensity={0.6} />
            <directionalLight
              position={[5, 5, 5]}
              intensity={1}
              castShadow
              shadow-mapSize-width={1024}
              shadow-mapSize-height={1024}
            />
            <directionalLight position={[-5, 5, 5]} intensity={0.8} />
            <pointLight position={[0, 2, 2]} intensity={0.6} />
            <hemisphereLight args={[0xffffff, 0x444444, 0.3]} />
            <CameraControls />
            <Suspense fallback={null}>
              <YogaModel
                selectedPose={selectedPose}
                onlyInAnimation={onlyInAnimation}
                isTTSSpeaking={isTTSSpeaking}
                isPaused={isPaused}
                staticMode={staticMode}
                staticModelPath={staticModelPath}
                playAnimationPath={playAnimationPath}
                playAnimationKey={playAnimationKey}
                onError={setError}
                onTTSSpeaking={onTTSSpeaking}
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
