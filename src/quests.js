import * as THREE from "three";
import { paint, stroke } from "./art.js";

// A small, complete exploration loop, kept separate from combat and NPC art.
// Objects are local geometry and can be replaced by painted assets later.
export class VillageActivities {
  constructor(scene, notify) {
    this.notify = notify;
    this.collected = 0;
    this.offered = false;
    this.started = false;
    this.blooms = [
      { id: "garden", name: "Garden windflower", x: -3, z: 7 },
      { id: "mill", name: "Mill windflower", x: -15, z: -13 },
      { id: "shrine", name: "Shrine windflower", x: 2, z: -12 },
    ].map((data, index) => {
      const root = new THREE.Group();
      root.position.set(data.x, 0, data.z);
      const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.032, 0.55, 5), paint("#476849"));
      stem.position.y = 0.28;
      root.add(stem);
      const flower = new THREE.Group();
      flower.position.y = 0.66;
      flower.rotation.x = -Math.PI / 2;
      for (let i = 0; i < 5; i++) {
        const petal = new THREE.Mesh(new THREE.CircleGeometry(0.17, 7), paint("#e08b84"));
        petal.material.side = THREE.DoubleSide;
        const angle = i * Math.PI * 2 / 5;
        petal.position.set(Math.cos(angle) * 0.13, Math.sin(angle) * 0.13, 0.006 + i * 0.001);
        petal.scale.set(0.75, 1.1, 1);
        petal.rotation.z = angle - Math.PI / 2;
        flower.add(petal);
      }
      const center = new THREE.Mesh(new THREE.CircleGeometry(0.07, 7), paint("#eac269"));
      center.material.side = THREE.DoubleSide;
      center.position.z = 0.02;
      flower.add(center);
      root.add(flower);
      const aura = new THREE.Mesh(
        new THREE.RingGeometry(0.45, 0.49, 24),
        new THREE.MeshBasicMaterial({ color: "#f0d787", transparent: true, opacity: 0.58, side: THREE.DoubleSide, depthWrite: false }),
      );
      aura.rotation.x = -Math.PI / 2;
      aura.position.y = 0.07;
      root.add(aura);
      scene.add(root);
      return { ...data, root, flower, aura, collected: false, phase: index * 1.8 };
    });
    this.shrine = { id: "offering", name: "Windflower shrine", root: new THREE.Group() };
    this.shrine.root.position.set(0, 0, -20);
    const mat = new THREE.MeshBasicMaterial({ color: "#e9c672", transparent: true, opacity: 0.48, side: THREE.DoubleSide, depthWrite: false });
    const ring = new THREE.Mesh(new THREE.RingGeometry(0.85, 0.89, 48), mat);
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.07;
    this.shrine.root.add(ring);
    stroke(this.shrine.root, [[-0.6,0.08,-0.6],[-0.3,0.08,-0.8],[0.3,0.08,-0.8],[0.6,0.08,-0.6]], "#a45235", 0.018);
    scene.add(this.shrine.root);
  }
  nearby(position) {
    let best = null, distance = 2.05;
    for (const target of [...this.blooms.filter((b) => !b.collected), this.shrine]) {
      const d = target.root.position.distanceTo(position);
      if (d < distance) { best = target; distance = d; }
    }
    return best;
  }
  prompt(target) {
    if (target.id !== "offering") return `E · Pick ${target.name.toLowerCase()}`;
    return this.offered ? "E · Rest at the shrine" : this.collected === 3 ? "E · Offer the three windflowers" : `E · Windflower shrine (${this.collected}/3 flowers)`;
  }
  interact(target, game) {
    if (target.id !== "offering") {
      if (target.collected) return;
      target.collected = true;
      target.root.visible = false;
      this.collected++;
      this.started = true;
      game.audio?.play("collect");
      game.effects.dust(target.root.position, { count: 8 });
      this.notify(this.collected === 3 ? "Three windflowers found · bring them to the northern shrine" : `${target.name} found · ${this.collected}/3 windflowers`);
      return;
    }
    if (this.offered) {
      const healed = game.hp < game.maxHp;
      game.hp = game.maxHp;
      game.audio?.play("heal");
      this.notify(healed ? "The shrine restores your vitality" : "The shrine's blessing is with you");
      game.effects.dust(target.root.position, { count: 9 });
      return;
    }
    if (this.collected < 3) {
      this.started = true;
      game.audio?.play("interact");
      this.notify("Find three windflowers: the garden, the mill path, and the shrine road");
      return;
    }
    this.offered = true;
    game.maxHp = 120;
    game.hp = 120;
    game.effects.burst(target.root.position, 22, "#edcc76");
    game.audio?.play("victory");
    this.notify("Shrine blessing earned · maximum vitality is now 120");
  }
  dialogueLines(npc, game) {
    if (npc.name.startsWith("Hana")) {
      this.started = true;
      if (this.offered) return ["The windflowers bloom again. Thank you, little guardian.", "The northern shrine will restore your vitality whenever you need it."];
      return ["The northern shrine has lost its flowers. Will you help it bloom?", "Find three pink windflowers: beside my garden, along the mill path, and on the road to the shrine. Press E to pick them.", this.collected === 3 ? "You found them all! Bring the flowers to the northern shrine for its blessing." : `You have ${this.collected} of three. An offering will strengthen your vitality before you enter the grove.`];
    }
    if (npc.name.startsWith("Elder")) return [game.victory ? "The grove's shadows are gone. The village can breathe again." : "Five restless spirits trouble the grove east of town. Watch them bow before they charge.", this.offered ? "Our shrine has blessed you. Rest there whenever your spirit is weary." : "An offering of three windflowers at the shrine will strengthen you."];
    if (npc.name.startsWith("Taro")) return [game.victory ? "Travelers are returning! Your spear made the road safe again." : "A thrust opens the way; a sweep breaks their guard; a lunge sends them home.", "Press again during a strike to prepare the next. Dodge with K before a charge reaches you."];
    if (npc.name.startsWith("Yui")) return ["I follow this road whenever the valley feels quiet.", "The pink windflowers shine in the grass. Use the mouse wheel to see them up close."];
    return npc.lines;
  }
  update(dt, time) {
    for (const bloom of this.blooms) {
      if (bloom.collected) continue;
      bloom.flower.rotation.z = Math.sin(time * 1.6 + bloom.phase) * 0.09;
      bloom.aura.material.opacity = 0.42 + Math.sin(time * 2.4 + bloom.phase) * 0.15;
      bloom.aura.scale.setScalar(1 + Math.sin(time * 2 + bloom.phase) * 0.08);
    }
    const aura = this.shrine.root.children[0];
    aura.material.opacity = this.offered ? 0.65 : this.collected === 3 ? 0.55 + Math.sin(time * 2) * 0.12 : 0.27;
  }
  get summary() {
    return this.offered ? "Shrine blessing · 120 vitality" : this.collected === 3 ? "Offer windflowers at the north shrine" : `Windflowers · ${this.collected} / 3`;
  }
}
