const BRANDS = [
  { id: 'oxdog', title: 'OXDOG' },
  { id: 'unihoc', title: 'UNIHOC' },
  { id: 'zone', title: 'ZONE' },
  { id: 'fatpipe', title: 'FATPIPE' }
];

let cachedSticks = null;

function renderBrands(includeAll = false) {
  const grid = document.getElementById('brands-grid');
  grid.innerHTML = '';
  const items = includeAll
    ? [{ id: 'all', title: 'Все клюшки' }, ...BRANDS]
    : BRANDS;

  items.forEach(brand => {
    const card = document.createElement('a');
    card.className = 'brand-card';
    card.href = '#';
    card.dataset.brand = brand.id;
    card.innerHTML = `<span class="brand-name">${brand.title}</span>`;
    card.addEventListener('click', e => {
      e.preventDefault();
      showModels(brand.id, brand.title);
    });
    grid.appendChild(card);
  });
}

async function fetchSticks() {
  if (cachedSticks) return cachedSticks;
  const res = await fetch('/api/sticks');
  if (!res.ok) throw new Error('Ошибка загрузки каталога');
  cachedSticks = await res.json();
  return cachedSticks;
}

function getModelName(stickName) {
  if (!stickName) return 'Модель';
  if (stickName.toUpperCase().includes('EXTREMEFAST')) return 'EXTREMEFAST';
  if (stickName.toUpperCase().includes('ULTIMATELIGHT')) return 'ULTIMATELIGHT';
  return 'Модель';
}

function renderModelCards(groups, onClick) {
  const grid = document.getElementById('sticks-grid');
  grid.innerHTML = '';

  groups.forEach(group => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <a href="#">
        <img src="/images/${group.photo}" alt="${group.name}" />
        <h3>${group.name}</h3>
        <span class="more">Подробнее →</span>
      </a>
    `;
    card.querySelector('a').addEventListener('click', e => {
      e.preventDefault();
      onClick(group);
    });
    grid.appendChild(card);
  });
}

async function showModels(brandId, title) {
  const section = document.getElementById('models-section');
  const grid = document.getElementById('sticks-grid');
  const heading = document.getElementById('models-title');

  heading.textContent = brandId === 'all' ? 'Все клюшки' : title;
  grid.innerHTML = '';

  let models = [];
  try {
    const sticks = await fetchSticks();
    if (brandId === 'all') {
      models = sticks;
    } else {
      const brandName = title.toUpperCase();
      models = sticks.filter(s => String(s.brand || '').toUpperCase() === brandName);
    }
    renderBrands(brandId !== 'all');
  } catch (e) {
    grid.innerHTML = '<p>Ошибка при загрузке каталога.</p>';
    console.error(e);
    section.hidden = false;
    return;
  }

  if (models.length === 0) {
    grid.innerHTML = '<p>Пока нет клюшек этого бренда.</p>';
    section.hidden = false;
    return;
  }

  if (brandId === 'all') {
    models.forEach(s => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <a href="/details.html?id=${encodeURIComponent(s.id)}">
          <img src="/images/${s.photo}" alt="${s.name}" />
          <h3>${s.name}</h3>
          <span class="more">Подробнее →</span>
        </a>
      `;
      grid.appendChild(card);
    });
  } else {
    const groupsMap = new Map();
    models.forEach(s => {
      const modelName = getModelName(s.name);
      if (!groupsMap.has(modelName)) {
        groupsMap.set(modelName, { name: modelName, photo: s.photo, items: [] });
      }
      groupsMap.get(modelName).items.push(s);
    });
    const groups = Array.from(groupsMap.values());
    renderModelCards(groups, group => showModelItems(title, group));
  }

  section.hidden = false;
  section.scrollIntoView({ behavior: 'smooth' });
}

function showModelItems(brandTitle, group) {
  const grid = document.getElementById('sticks-grid');
  const heading = document.getElementById('models-title');
  heading.textContent = `${brandTitle} — ${group.name}`;
  grid.innerHTML = '';

  group.items.forEach(s => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <a href="/details.html?id=${encodeURIComponent(s.id)}">
        <img src="/images/${s.photo}" alt="${s.name}" />
        <h3>${s.name}</h3>
        <span class="more">Подробнее →</span>
      </a>
    `;
    grid.appendChild(card);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  renderBrands();
  showModels('all', '');
});
