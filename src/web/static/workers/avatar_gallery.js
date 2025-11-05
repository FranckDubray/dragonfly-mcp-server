





export function createAvatarGallery({ initial="", onChange } = {}){
  const box = document.createElement('div');
  box.className = 'avatar-grid';
  let selected = String(initial||'').trim();

  function render(items){
    box.innerHTML = '';
    items.forEach(name => {
      const it = document.createElement('div');
      it.className = 'avatar-item';
      it.setAttribute('data-name', name);
      it.tabIndex = 0;
      const img = document.createElement('img');
      img.src = `/docs/images/${encodeURIComponent(name)}`;
      img.alt = name;
      it.appendChild(img);
      if (name === selected) it.classList.add('selected');
      const choose = () => {
        selected = name;
        Array.from(box.querySelectorAll('.avatar-item.selected')).forEach(n => n.classList.remove('selected'));
        it.classList.add('selected');
        onChange && onChange(selected);
      };
      it.addEventListener('click', choose);
      it.addEventListener('keydown', (e)=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); choose(); }});
      box.appendChild(it);
    });
  }

  async function load(){
    try{
      const r = await fetch('/workers/api/avatars');
      const js = await r.json();
      const items = Array.isArray(js.images) ? js.images : [];
      render(items);
    }catch{
      box.textContent = 'Aucune image trouvée';
    }
  }

  load();

  return {
    el: box,
    getSelected: ()=> selected,
    setSelected: (name)=>{ selected = String(name||'').trim(); load(); }
  };
}
