export type YogaPoseAnimation = {
  inPath: string;
  mainPath: string;
  outPath: string;
};

/**
 * How a pose behaves while it is being held.
 *
 * MAIN clips loop for the whole hold by default, which is right for a pose that
 * keeps moving (Cat and Camel alternates between the two shapes). For a static
 * hold the looping motion is wrong - the authored clip drifts, so the body
 * visibly keeps shifting when it should have settled. `freezeMain` plays the
 * clip once and holds its final frame instead.
 */
export type YogaPoseHold = {
  freezeMain?: boolean;
};

export const YOGA_POSE_HOLD: Record<string, YogaPoseHold> = {
  // Reported: the belly and hips keep moving through the whole hold.
  "Cobra Pose": { freezeMain: true },
  // Reported: the held position never settles.
  "Warrior 1": { freezeMain: true },
};

export function shouldFreezeMainPose(poseName: string | undefined): boolean {
  if (!poseName) return false;
  return YOGA_POSE_HOLD[poseName]?.freezeMain === true;
}

export const YOGA_POSE_ANIMATIONS: Record<string, YogaPoseAnimation> = {
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
    inPath: "/Mountain Pose/in_compressed1.glb",
    mainPath: "/Mountain Pose/main_compressed1.glb",
    outPath: "/Mountain Pose/out_compressed1.glb",
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
