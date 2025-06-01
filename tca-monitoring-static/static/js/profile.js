Promise.all([
  fetch('static/data/user_data.json').then(res => res.json()),
  fetch('static/data/tiktok_metadata.json').then(res => res.json()),
  fetch('static/data/alerts.json').then(res => res.json())
]).then(([userData, tiktokData, alerts]) => {
  const user = userData.users[USER_INDEX];
  const metadata = Object.values(tiktokData.metadata || {});
  const descriptions = metadata.map(v => (v.description || '').toLowerCase());

  const foundWords = new Set();
  descriptions.forEach(desc => {
    TCA_KEYWORDS.forEach(word => {
      if (desc.includes(word)) {
        foundWords.add(word);
      }
    });
  });

  const container = document.getElementById('profile-container');
  container.innerHTML = `
    <h2>Profil de ${user.name}</h2>
    <p>Vidéos analysées : ${descriptions.length}</p>
    <p>Mots problématiques détectés : ${foundWords.size}</p>
    <ul>${[...foundWords].map(w => `<li>${w}</li>`).join('')}</ul>
    
    <h3>Graphiques</h3>
    <img src="static/img/hashtags_barplot.png" alt="Hashtags">
    <img src="static/img/category_graph.png" alt="Catégories">
    <img src="static/img/popular_trends.png" alt="Tendances">
    <img src="static/img/popular_influencers_communities.png" alt="Influenceurs">

    <h3>Alertes</h3>
    <ul>
      <li><strong>Tendances :</strong> ${alerts.trends_alert.join(', ')}</li>
      <li><strong>Influenceurs :</strong> ${alerts.influencers_alert.join(', ')}</li>
      <li><strong>Fréquence :</strong> ${alerts.frequency_alerts.join(', ')}</li>
    </ul>
  `;
});
