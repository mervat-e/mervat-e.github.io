const TCA_KEYWORDS = [ "anorexie", "anorexia", "boulimie", "bulimia", "tca", "eating disorder", "trouble alimentaire",
"skinny", "maigre", "mince", "mincir", "maigrir", "corps parfait", "objectif poids", "objectif minceur",
"poids idéal", "corps de rêve", "ventre plat", "thigh gap", "flat stomach", "zero fat", "collarbones",
"ribs", "bones", "visible ribs", "skinny waist", "skinny arms",
"régime", "calorie", "calories", "0 calories", "zero calorie", "low carb", "low fat", "no carbs", "sans sucre",
"fasting", "intermittent fasting", "jeûne", "jeûner", "starvation", "meal skipping", "skip meals", "no eating",
"rien manger", "ne pas manger",
"vomir", "vomissement", "purge", "laxatif", "laxatifs", "diurétique", "diurétiques", "surentraînement", "exercise excessif",
"proana", "pro-ana", "promia", "pro-mia", "ana tips", "ana tricks", "ana goals", "ana buddy",
"thinspiration", "thinspo", "fitspiration", "bonespo", "fitspo",
"body check", "trigger warning", "feel fat", "je me sens grosse", "je me sens trop gros",
"détestation de soi", "perte de poids rapide", "challenge poids", "dégout de nourriture"
]; 

function containsTCAKeyword(description) {
  return TCA_KEYWORDS.filter(word => description.includes(word));
}
