"use client";
import React, { useEffect, useState, useRef, Suspense } from "react";
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
  "Mountain Pose": { in: 4, hold: 25, out: 3, angle: 90 },
  "Tree Pose": { in: 6, hold: 30, out: 5, angle: 90 },
  "Downward Dog": { in: 7, hold: 30, out: 6, angle: 180 },
  "Warrior 1": { in: 8, hold: 30, out: 6, angle: 270 },
  "Warrior Pose": { in: 7, hold: 30, out: 6, angle: 270 }, // Warrior II
  "Triangle": { in: 8, hold: 25, out: 6, angle: 180 },
  "Child Pose": { in: 5, hold: 35, out: 5, angle: 180 },
  "Cobra Pose": { in: 6, hold: 20, out: 6, angle: 180 },
  "Cat And Camel Pose": { in: 4, hold: 40, out: 4, angle: 180 },
  "Seated Forward": { in: 7, hold: 35, out: 7, angle: 180 },
};

const POSE_ANIMATIONS: Record<string, PoseAnimation> = {
  "Downward Dog": {
    inPath: "/Downward Dog Pose/downward_dog_in_compressed.glb",
    mainPath: "/Downward Dog Pose/downward_dog_main_compressed.glb",
    outPath: "/Downward Dog Pose/downward_dog_out_compressed.glb",
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
    inPath: "/Cat And Camel Pose/Cat and Camel pose-IN_compressed.glb",
    mainPath: "/Cat And Camel Pose/Cat and Camel pose-MAIN_compressed.glb",
    outPath: "/Cat And Camel Pose/Cat and Camel pose-OUT_compressed.glb",
  },
  "Child Pose": {
    inPath: "/Child Pose/child_pose_in_compressed.glb",
    mainPath: "/Child Pose/child_pose_main_compressed.glb",
    outPath: "/Child Pose/child_pose_out_compressed.glb",
  },
  "Cobra Pose": {
    inPath: "/Cobra Pose/in_compressed.glb",
    mainPath: "/Cobra Pose/main_compressed.glb",
    outPath: "/Cobra Pose/out_compressed.glb",
  },
  "Seated Forward": {
    inPath: "/Seated Forward Pose/seated_forward_in_compressed.glb",
    mainPath: "/Seated Forward Pose/seated_forward_main_compressed.glb",
    outPath: "/Seated Forward Pose/seated_forward_out_compressed.glb",
  },
  "Warrior 1": {
    inPath: "/Warrior 1 Pose/warrior_1_in_compressed.glb",
    mainPath: "/Warrior 1 Pose/warrior_1_main_compressed.glb",
    outPath: "/Warrior 1 Pose/warrior_1_out_compressed.glb",
  },
};

function YogaModel({ selectedPose, onlyInAnimation = false, isTTSSpeaking = false, isPaused = false, staticMode = false, staticModelPath, playAnimationPath, playAnimationKey, onError }: { selectedPose: string; onlyInAnimation?: boolean; isTTSSpeaking?: boolean; isPaused?: boolean; staticMode?: boolean; staticModelPath?: string; playAnimationPath?: string; playAnimationKey?: number; onError?: (error: string) => void }) {
  const [model, setModel] = useState<THREE.Group | null>(null);
  const [mixer, setMixer] = useState<THREE.AnimationMixer | null>(null);
  const [currentAnimation, setCurrentAnimation] = useState<'in' | 'main' | 'out'>('in');
  const meshRef = useRef<THREE.Group>(null);
  const animationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const currentPoseRef = useRef<string>('');
  const scene = useThree((state) => state.scene); // Get scene from useThree hook

  // TTS blendshape animation
  const blendshapeMeshRef = useRef<THREE.Mesh | null>(null);
  const blendshapeNamesRef = useRef<string[]>([]);
  const originalBlendshapesRef = useRef<number[]>([]);

  // Load chess avatar without animations
  const loadChessAvatar = async (modelPath?: string) => {
    try {
      const loader = new GLTFLoader();
      
      // Set up DRACOLoader for compressed files
      const dracoLoader = new DRACOLoader();
      dracoLoader.setDecoderPath('/draco/');
      loader.setDRACOLoader(dracoLoader);

      // Set up KTX2Loader for texture compression
      const ktx2Loader = new KTX2Loader()
        .setTranscoderPath('/basis/')
        .detectSupport(new THREE.WebGLRenderer());
      loader.setKTX2Loader(ktx2Loader);

      console.log('Loading static avatar...');
      
      // Load yoga avatar as static model (use in animation)
      const gltf = await loader.loadAsync(modelPath || '/Mountain Pose/in_compressed.glb');
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

      loadedModel.position.set(0, -1, 0);
      setModel(loadedModel);
      console.log('Static avatar loaded successfully');
    } catch (error) {
      console.error('Error loading static avatar:', error);
      onError?.('Failed to load static avatar');
    }
  };

  useEffect(() => {
    // If static mode, load chess avatar without animations
    if (staticMode) {
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

    // Set up DRACOLoader for compressed files
    const dracoLoader = new DRACOLoader();
    dracoLoader.setDecoderPath('/draco/');
    loader.setDRACOLoader(dracoLoader);

    // Set up KTX2Loader for texture compression
    const ktx2Loader = new KTX2Loader()
      .setTranscoderPath('/basis/')
      .detectSupport(new THREE.WebGLRenderer());
    loader.setKTX2Loader(ktx2Loader);

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
        
        // Set up DRACOLoader for compressed files
        const dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('/draco/');
        loader.setDRACOLoader(dracoLoader);

        // Set up KTX2Loader for texture compression
        const ktx2Loader = new KTX2Loader()
          .setTranscoderPath('/basis/')
          .detectSupport(new THREE.WebGLRenderer());
        loader.setKTX2Loader(ktx2Loader);

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
        
        // Create animation mixer but don't play any animations for static mode
        const animationMixer = new THREE.AnimationMixer(loadedModel);
        setMixer(animationMixer);
        
      } catch (error) {
        console.error('Error loading static avatar:', error);
      }
    }

    async function playAnimationSequence(pose: PoseAnimation, type: 'in' | 'main' | 'out') {
      try {
        // Reset rotation to front-facing on every transition
        if (meshRef.current) {
          meshRef.current.rotation.y = 0; // 0 rad = 90 deg = Front-facing
        }

        const gltf = await new Promise<any>((resolve, reject) => {
          const path = type === 'in' ? pose.inPath : type === 'main' ? pose.mainPath : pose.outPath;
          loader.load(path, resolve, undefined, reject);
        });

        const loadedModel = gltf.scene;

        // Clean up previous mixer
        if (mixer) {
          mixer.stopAllAction();
          mixer.uncacheRoot(loadedModel);
        }

        // Set up animation mixer
        const animationMixer = new THREE.AnimationMixer(loadedModel);
        setMixer(animationMixer);

        // Find blendshapes for mouth animation - prioritize body_1 mesh (main face)
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
            if (isMainFaceMesh || 
                (isMouthMesh && !blendshapeMeshRef.current) ||
                (!blendshapeMeshRef.current && child.morphTargetInfluences.length > 0) ||
                (child.morphTargetInfluences && child.morphTargetInfluences.length > (blendshapeMeshRef.current?.morphTargetInfluences?.length || 0))) {
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
              
              // console.log('Found blendshape mesh:', child.name, 'with', blendshapeNamesRef.current.length, 'blendshapes (isMainFaceMesh:', isMainFaceMesh, ', isMouthMesh:', isMouthMesh, ')');
              // console.log('Available blendshapes:', blendshapeNamesRef.current);
            }
          }
        });

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

            if (onlyInAnimation) {
              // For yoga session - play full animation sequence like normal yoga mode
              if (type === 'main') {
                action.setLoop(THREE.LoopRepeat, Infinity);
                action.clampWhenFinished = false;
              } else {
                action.setLoop(THREE.LoopOnce, 1);
                action.clampWhenFinished = true;
              }
              console.log(`Playing clip: ${clip.name}, type: ${type}, duration: ${clip.duration}s (yoga session mode)`);
            } else {
              // For normal page load - play only once and stop at last position
              action.setLoop(THREE.LoopOnce, 1);
              action.clampWhenFinished = true;
              console.log(`Playing clip: ${clip.name}, duration: ${clip.duration}s (play once - static mode)`);
            }

            action.play();
            maxDuration = Math.max(maxDuration, clip.duration);
          });

        // Handle transitions based on spec timing
          if (onlyInAnimation) {
            // Yoga session - handle transitions like normal yoga mode
            const spec = POSE_SPEC[selectedPose];
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
                }, spec.out * 1000);
              }
            }
          } else {
            // Normal page load - no transitions, just play in animation once and stop
          }
        } else {
          console.warn(`No animations found in ${type} GLB file`);
        }

        // Set shadows and materials
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

    const playChessAnimation = async () => {
      try {
        console.log('🎬 Playing chess animation:', playAnimationPath);
        const loader = new GLTFLoader();

        const dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('/draco/');
        loader.setDRACOLoader(dracoLoader);

        const ktx2Loader = new KTX2Loader()
          .setTranscoderPath('/basis/')
          .detectSupport(new THREE.WebGLRenderer());
        loader.setKTX2Loader(ktx2Loader);

        const gltf = await loader.loadAsync(playAnimationPath);
        if (isCancelled) {
          return;
        }

        const loadedModel = gltf.scene;

        if (mixer) {
          mixer.stopAllAction();
          mixer.uncacheRoot(loadedModel);
        }

        const animationMixer = new THREE.AnimationMixer(loadedModel);
        setMixer(animationMixer);

        let maxDuration = 0;
        if (gltf.animations && gltf.animations.length > 0) {
          console.log('🎭 Found animations:', gltf.animations.map(a => a.name));
          gltf.animations.forEach((clip: THREE.AnimationClip) => {
            const action = animationMixer.clipAction(clip);
            action.setLoop(THREE.LoopOnce, 1);
            action.clampWhenFinished = true;
            action.play();
            maxDuration = Math.max(maxDuration, clip.duration);
          });
        } else {
          console.warn('No animations found in chess gesture model');
        }

        loadedModel.position.set(0, -1, 0);
        loadedModel.scale.setScalar(1.2);
        setModel(loadedModel);

        if (animationTimeoutRef.current) {
          clearTimeout(animationTimeoutRef.current);
        }

        if (maxDuration > 0) {
          animationTimeoutRef.current = setTimeout(() => {
            if (animationMixer) {
              animationMixer.stopAllAction();
            }
          }, maxDuration * 1000);
        }
      } catch (error) {
        console.error('Error playing chess animation:', error);
      }
    };

    playChessAnimation();

    return () => {
      isCancelled = true;
      if (animationTimeoutRef.current) {
        clearTimeout(animationTimeoutRef.current);
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

      // TTS blendshape animation (only if not paused)
      if (isTTSSpeaking && !isPaused && blendshapeMeshRef.current && blendshapeMeshRef.current.morphTargetInfluences) {
        const time = state.clock.elapsedTime;
        
        // Look for mouth-related blendshapes - expanded list with visemes
        const mouthBlendshapes = blendshapeNamesRef.current.filter(name => 
          name.toLowerCase().includes('mouth') || 
          name.toLowerCase().includes('jaw') || 
          name.toLowerCase().includes('lip') ||
          name.toLowerCase().includes('tongue') ||
          name.toLowerCase().includes('viseme')
        );
        
        if (mouthBlendshapes.length > 0) {
          // Natural human-like animation
          mouthBlendshapes.forEach((blendshapeName, index) => {
            const morphIndex = blendshapeMeshRef.current!.morphTargetDictionary?.[blendshapeName];
            if (morphIndex !== undefined && blendshapeMeshRef.current!.morphTargetInfluences) {
              // Natural talking animation - much more subtle
              const baseValue = Math.abs(Math.sin(time * 3 + index)) * 0.3; // Reduced intensity
              const variation = Math.sin(time * 6 + index * 0.2) * 0.15; // Less variation
              const finalValue = Math.min(0.6, baseValue + variation); // Max 0.6 for natural look
              
              // Special handling for key mouth blendshapes - more natural values
              if (blendshapeName.toLowerCase().includes('jawopen') || 
                  blendshapeName.toLowerCase().includes('mouthopen')) {
                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = finalValue * 0.8; // Natural jaw opening
              } else if (blendshapeName.toLowerCase().includes('mouthclose')) {
                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = finalValue * 0.2; // Less closing
              } else if (blendshapeName.toLowerCase().includes('tongueout')) {
                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = finalValue * 0.4; // Natural tongue movement
              } else if (blendshapeName.toLowerCase().includes('viseme')) {
                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = finalValue * 0.6; // Subtle viseme animation
              } else {
                blendshapeMeshRef.current!.morphTargetInfluences[morphIndex] = finalValue * 0.5; // General mouth movement
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
      } else if (!isTTSSpeaking && blendshapeMeshRef.current && blendshapeMeshRef.current.morphTargetInfluences) {
        // Return to original blendshape values when not speaking
        blendshapeMeshRef.current.morphTargetInfluences.forEach((value, index) => {
          const originalValue = (originalBlendshapesRef.current && originalBlendshapesRef.current[index]) || 0;
          if (blendshapeMeshRef.current && blendshapeMeshRef.current.morphTargetInfluences) {
            blendshapeMeshRef.current.morphTargetInfluences[index] = THREE.MathUtils.lerp(value, originalValue, 0.1);
          }
        });
      }

      // Smooth rotation to target angle
      const spec = POSE_SPEC[selectedPose];
      if (spec) {
        // Spec: 90=Front, 180=Right Profile, 270=Back, 360=Left Profile
        // Micro-demo: Show side view (180 or 360) for first few seconds of Hold or during In phase.

        let targetAngle = spec.angle;

        // Tricky poses: Mountain, Warrior, Downward Dog, Cat Cow etc.
        const isTricky = ["Warrior 1", "Warrior Pose", "Downward Dog", "Cat And Camel Pose"].includes(selectedPose);

        if (isTricky && currentAnimation === 'in') {
          // Force side view during transition in
          targetAngle = 180;
        }

        const targetRad = (targetAngle - 90) * (Math.PI / 180);

        // Max rotation speed: 10-15 deg/s
        const maxStep = (15 * Math.PI / 180) * delta;

        // Smoothly rotate
        const diff = targetRad - meshRef.current.rotation.y;
        if (Math.abs(diff) > 0.001) {
          meshRef.current.rotation.y += Math.sign(diff) * Math.min(Math.abs(diff), maxStep);
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
}

export default function Avatar3D({ selectedPose = "Mountain Pose", onlyInAnimation = false, isTTSSpeaking = false, isPaused = false, staticMode = false, staticModelPath, playAnimationPath, playAnimationKey }: Avatar3DProps) {
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
    console.log('WebGL supported:', !!gl);
  }, []);

  // Always show a fallback for walktour purposes
  return (
    <div className="w-full h-full flex items-center justify-center" style={{ position: "relative" }} data-walktour="avatar">
      {/* Try to load 3D avatar */}
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
            {/* Lights */}
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
