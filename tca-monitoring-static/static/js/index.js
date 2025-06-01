fetch('static/data/user_data.json')
  .then(res => res.json())
  .then(data => {
    const users = data.users;
    const container = document.getElementById('user-list');
    users.forEach((user, index) => {
      const div = document.createElement('div');
      div.innerHTML = `<a href="profile${index === 0 ? '2' : ''}.html">${user.name}</a>`;
      container.appendChild(div);
    });
  });
