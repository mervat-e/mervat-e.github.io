document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("user-list");

  fetch("static/data/user_data.json")
    .then((res) => {
      if (!res.ok) {
        throw new Error(`Erreur HTTP : ${res.status}`);
      }
      return res.json();
    })
    .then((data) => {
      if (!data.users || !Array.isArray(data.users)) {
        throw new Error("Format de données invalide : 'users' manquant ou incorrect.");
      }

      data.users.forEach((user, index) => {
        const link = document.createElement("a");
        link.href = index === 0 ? "profile_2.html" : "profile.html";
        link.textContent = user.name || `Utilisateur ${index + 1}`;
        link.style.display = "block"; // pour les empiler verticalement
        container.appendChild(link);
      });
    })
    .catch((err) => {
      container.textContent = `Erreur lors du chargement des utilisateurs : ${err.message}`;
      console.error("Erreur dans index.js :", err);
    });
});
