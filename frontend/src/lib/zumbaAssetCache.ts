// Shared GLTF loading + caching for the Zumba avatar player.
//
// Responsibilities:
//  - Configure a single GLTFLoader with DRACO + KTX2 support (matches Avatar3D).
//  - Cache parsed GLTFs by URL so a move is only fetched + parsed once.
//  - Clone prepared, animation-ready scenes for runtime use (SkeletonUtils).
//
// GPU warm-up lives in ZumbaAvatarPlayer because it needs the live renderer.

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js';
import * as SkeletonUtils from 'three/examples/jsm/utils/SkeletonUtils.js';

// three caches loaded ArrayBuffers globally; disable so GLB buffers don't pile
// up in the JS heap across sessions (browser HTTP cache still avoids re-fetch).
THREE.Cache.enabled = false;

type LoadedGltf = {
  scene: THREE.Group;
  animations: THREE.AnimationClip[];
};

export class ZumbaAssetCache {
  private loader: GLTFLoader;
  private draco: DRACOLoader;
  private ktx2: KTX2Loader | null = null;
  private gltfCache = new Map<string, Promise<LoadedGltf>>();

  constructor() {
    this.loader = new GLTFLoader();
    this.draco = new DRACOLoader();
    this.draco.setDecoderPath('/draco/');
    this.loader.setDRACOLoader(this.draco);
  }

  /** Wire up KTX2 transcoding once the renderer exists. */
  attachRenderer(renderer: THREE.WebGLRenderer): void {
    if (this.ktx2) return;
    try {
      this.ktx2 = new KTX2Loader().setTranscoderPath('/basis/').detectSupport(renderer);
      this.loader.setKTX2Loader(this.ktx2);
    } catch {
      this.ktx2 = null;
    }
  }

  /** Fetch + parse a GLB once. Subsequent calls reuse the same promise. */
  loadGltf(url: string): Promise<LoadedGltf> {
    let pending = this.gltfCache.get(url);
    if (!pending) {
      pending = this.loader.loadAsync(url).then((gltf) => ({
        scene: gltf.scene as THREE.Group,
        animations: gltf.animations as THREE.AnimationClip[],
      }));
      pending.catch(() => this.gltfCache.delete(url));
      this.gltfCache.set(url, pending);
    }
    return pending;
  }

  /**
   * Clone a parsed GLTF scene into an independent, animation-ready instance.
   * Clones are deep (SkeletonUtils) so each instance has its own skeleton and
   * can run its own mixer without disturbing the cached source.
   */
  cloneScene(loaded: LoadedGltf): THREE.Group {
    const clone = SkeletonUtils.clone(loaded.scene) as THREE.Group;
    clone.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.castShadow = true;
        child.receiveShadow = true;
        // Skinned meshes keep their bind-pose bounding volume, so when the
        // animation moves bones (and the camera is zoomed in) Three.js culls
        // them mid-session — hair vanishes first, then the whole avatar.
        // Disable culling so the avatar is always drawn.
        child.frustumCulled = false;
        // SkeletonUtils.clone shares materials by reference. Clone them per
        // instance so skin tone + opacity crossfade don't bleed across moves.
        if (Array.isArray(child.material)) {
          child.material = child.material.map((m) => m.clone());
        } else if (child.material) {
          child.material = child.material.clone();
        }
        const mat = Array.isArray(child.material) ? child.material[0] : child.material;
        if (mat && (mat as THREE.MeshStandardMaterial).map) {
          (mat as THREE.MeshStandardMaterial).map!.anisotropy = 4;
        }
      }
    });
    return clone;
  }

  dispose(): void {
    this.gltfCache.clear();
    try { this.draco.dispose(); } catch { /* noop */ }
    try { this.ktx2?.dispose(); } catch { /* noop */ }
    this.ktx2 = null;
  }
}
