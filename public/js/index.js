async function loadSticks() {
  const grid = document.getElementById('sticks-grid');
  grid.innerHTML = 'Загрузка...';
  try {
    const res = await fetch('/api/sticks');
    if (!res.ok) throw new Error('Ошибка загрузки');
    const sticks = await res.json();
    grid.innerHTML = '';
    sticks.forEach(s => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <a href="/details.html?id=${encodeURIComponent(s.id)}">
          <img src="/images/${s.photo}" alt="${s.name}" />
          <h3>${s.name}</h3>
        </a>
      `;
      grid.appendChild(card);
    });
    if (sticks.length === 0) grid.innerHTML = '<p>Нет клюшек в каталоге.</p>';
  } catch (e) {
    grid.innerHTML = '<p>Ошибка при загрузке каталога.</p>';
    console.error(e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadSticks();
});
