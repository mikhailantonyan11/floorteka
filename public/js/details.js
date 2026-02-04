function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

async function loadDetails() {
  const id = getQueryParam('id');
  if (!id) {
    document.getElementById('stick-name').textContent = 'Клюшка не найдена';
    return;
  }

  try {
    const res = await fetch('/api/sticks/' + encodeURIComponent(id));
    if (res.status === 404) {
      document.getElementById('stick-name').textContent = 'Клюшка не найдена';
      return;
    }
    if (!res.ok) throw new Error('Ошибка сервера');
    const s = await res.json();

    document.getElementById('stick-name').textContent = s.name;
    document.getElementById('stick-photo').src = '/images/' + s.photo;
    document.getElementById('stick-photo').alt = s.name;
    document.getElementById('stick-title').textContent = s.name;
    const ul = document.getElementById('stick-features');
    ul.innerHTML = '';
    (s.features || []).forEach(f => {
      const li = document.createElement('li');
      li.textContent = f;
      ul.appendChild(li);
    });
  } catch (e) {
    document.getElementById('stick-name').textContent = 'Ошибка при загрузке';
    console.error(e);
  }
}

document.addEventListener('DOMContentLoaded', loadDetails);
