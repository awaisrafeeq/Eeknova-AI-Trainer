export interface YogaPhaseInstruction {
  in: string;
  mainIntro?: string;
  out: string;
}

export const YOGA_PHASE_INSTRUCTIONS: Record<string, YogaPhaseInstruction> = {
  "Mountain Pose": {
    in: "Stand comfortably with your feet together. Spread your toes, relax your shoulders, and grow tall through the crown of your head. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Tree Pose": {
    in: "Shift your weight onto one foot. Place the other foot on your calf or inner thigh, then bring your hands together and focus on one point. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Downward Dog": {
    in: "Place your hands on the mat, step your feet back, and lift your hips up and back. Keep your knees soft if you need to. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Warrior 1": {
    in: "Clasp your hands and rotate outward. Step one leg far back onto the toes, bend your front knee, and raise your arms overhead. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Warrior Pose": {
    in: "Step your feet wide apart. Bend your front knee, stretch your arms out to the sides, and gently look over your front hand. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Triangle Pose": {
    in: "Straighten your front leg and reach forward gently. Rest your hand on your shin or ankle, then lift your other arm and open your chest. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Child Pose": {
    in: "Lower your knees to the mat. Sit your hips back toward your heels, reach your arms forward, and rest your forehead down. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Cobra Pose": {
    in: "Lie down on your stomach and place your hands under your shoulders. Press lightly into your palms and lift your chest gently. Hold for the required time.",
    out: "Return to the original position.",
  },
  "Cat And Camel Pose": {
    // Both halves are spoken while entering the pose. They used to be split, so
    // the movement itself was only explained after the hold had already begun -
    // by which point the user was expected to be doing it.
    in: "Come into all fours with your hands under your shoulders and knees under your hips. Make sure your elbows do not bend. Then round your spine up into Cat, lower your belly and lift your chest into Camel, and keep moving between the two.",
    out: "Return to the original position.",
  },
  "Seated Forward": {
    in: "Sit with your legs stretched out in front. Sit tall, then slowly bend forward from your hips only as far as feels comfortable. Hold for the required time.",
    out: "Return to the original position.",
  },
};

export function getYogaPhaseInstruction(
  poseName: string,
  phase: keyof YogaPhaseInstruction
): string | null {
  return YOGA_PHASE_INSTRUCTIONS[poseName]?.[phase] || null;
}

export function estimateInstructionDurationSeconds(text: string | null | undefined): number | undefined {
  if (!text) return undefined;
  const wordCount = text.split(/\s+/).filter(Boolean).length;
  const sentencePauses = Math.max(0, (text.match(/[.!?]/g) || []).length - 1) * 0.25;
  return Math.max(3.2, wordCount * 0.31 + sentencePauses + 0.4);
}
