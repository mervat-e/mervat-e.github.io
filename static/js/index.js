document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("user-list");

  const users = [
    { path: "static/data/user_data_tiktok_1.json", link: "profile_2.html" },
    { path: "static/data/user_data_tiktok_2.json", link: "profile.html" }
  ];

  users.forEach(({ path, link }, index) => {
    fetch(path)
      .then((res) => {
        if (!res.ok) throw new Error(`Erreur HTTP ${res.status} pour ${path}`);
        return res.json();
      })
      .then((data) => {
        const profile = data["Profile And Settings"]?.["Profile Info"]?.["ProfileMap"];
        if (!profile) throw new Error("Profil introuvable");

        const userName = profile.userName || `Utilisateur ${index + 1}`;
        const img = profile.profilePhoto || null;

        const a = document.createElement("a");
        a.href = link;
        a.style.display = "flex";
        a.style.alignItems = "center";
        a.style.gap = "10px";
        a.style.marginBottom = "10px";

        if (img) {
          const pic = document.createElement("img");
          pic.src = img;
          pic.alt = userName;
          pic.style.width = "40px";
          pic.style.height = "40px";
          pic.style.borderRadius = "50%";
          a.appendChild(pic);
        }

        const span = document.createElement("span");
        span.textContent = userName;
        a.appendChild(span);

        container.appendChild(a);
      })
      .catch((err) => {
        console.error("Erreur de chargement utilisateur :", err);
        const errorMsg = document.createElement("p");
        errorMsg.textContent = `Erreur lors du chargement de ${path}`;
        errorMsg.style.color = "red";
        container.appendChild(errorMsg);
      });
  });
});
