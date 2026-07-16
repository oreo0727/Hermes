(function(){
  // Minimal narrative system: a few events with choices that set flags.
  const STORIES = [
    {
      id: 'grove',
      text: 'A quiet grove opens between the hedges. Fireflies trace lazy constellations. A mossy journal lies half-buried at your feet.',
      choices: [
        { id:'read', label:'Read the journal', effect:(flags)=>{ flags.readJournal = true; } },
        { id:'leave', label:'Leave it undisturbed', effect:(flags)=>{ flags.steward = true; } },
      ]
    },
    {
      id: 'lantern',
      text: 'You find a small lantern, still warm to the touch. The air smells faintly of tea and rain.',
      choices: [
        { id:'light', label:'Light the lantern', effect:(flags)=>{ flags.hasLight = true; } },
        { id:'pocket', label:'Pocket the lantern for later', effect:(flags)=>{ flags.resourceful = true; } },
      ]
    },
    {
      id: 'signpost',
      text: 'A weathered signpost points in two directions: Home and Wonder. The paint has run, but the words still sing.',
      choices: [
        { id:'home', label:'Face Home', effect:(flags)=>{ flags.homesick = true; } },
        { id:'wonder', label:'Chase Wonder', effect:(flags)=>{ flags.wander = true; } },
      ]
    }
  ];

  // Given a path (array of [r,c]), choose a few spaced positions for story nodes.
  function placeStoryNodes(path, grid){
    const nodes = [];
    if(!path || path.length<8) return nodes;
    const picks = [0.25, 0.6, 0.85];
    const used = new Set();
    for(let i=0;i<picks.length;i++){
      const idx = Math.min(path.length-1, Math.max(1, Math.floor(path.length*picks[i])));
      const key = path[idx][0]+','+path[idx][1];
      if(used.has(key)) continue; used.add(key);
      const story = STORIES[i % STORIES.length];
      nodes.push({ r:path[idx][0], c:path[idx][1], storyId:story.id });
    }
    return nodes;
  }

  function getStoryById(id){ return STORIES.find(s=>s.id===id); }

  window.Narrative = { placeStoryNodes, getStoryById };
})();
