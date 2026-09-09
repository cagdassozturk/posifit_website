import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';
import { BoxHelper } from 'three';



// === INITIAL SETUP ===
const canvas = document.getElementById('c');
const scene = new THREE.Scene();

const camera = new THREE.PerspectiveCamera(100, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 0, 6);
scene.add(camera);

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1;
renderer.outputEncoding = THREE.sRGBEncoding;

// === LIGHTS ===
const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffffff, 0.2);
dirLight.position.set(5, 5, 5);
scene.add(dirLight);

// === HELPERS ===
const axesHelper = new THREE.AxesHelper(2);
scene.add(axesHelper);

const gridHelper = new THREE.GridHelper(10, 10);
scene.add(gridHelper);

// === LOAD ENVIRONMENT ===
new RGBELoader()
  .setPath('model/')
  .load('environment.hdr', function (hdrTexture) {
    hdrTexture.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = hdrTexture;
    loadModel();
  });

// === LOAD MODEL ===
// === LOAD MODEL + INIT SCROLL ANIMATION ===
let model;
function loadModel() {
  const loader = new GLTFLoader();
  loader.load('model/LEGOFIT_model.glb', gltf => {
    model = gltf.scene;

    model.traverse(node => {
      if (node.isMesh) {
        node.material.metalness = 0.3;
        node.material.roughness = 0.4;
        node.material.envMapIntensity = 1.5;
        node.castShadow = node.receiveShadow = true;
      }
    });

    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    console.log('Model size:', size, 'Center:', center);

    model.position.sub(center);
    model.scale.set(5, 5);
    scene.add(model);

    const helper = new BoxHelper(model, 0xff0000);
    scene.add(helper);

    camera.position.set(0, 0, Math.max(size.x, size.y, size.z) * 2);
    camera.lookAt(0, 0, 0);

    setupScrollAnimation(); // Hook in scroll animation now
  });
}
// === GSAP SCROLL-TRIGGERED MOTION ===
function setupScrollAnimation() {
  gsap.to(model.rotation, {
    y: "+=" + Math.PI * 2,
    scrollTrigger: {
      trigger: "#landing",
      start: "top bottom",
      end: "bottom top",
      scrub: true,
    }
  });

  gsap.to(model.position, {
    z: "-=0.2",
    scrollTrigger: {
      trigger: "#section1",
      start: "top bottom",
      end: "bottom top",
      scrub: true,
    }
  });
}

// === RENDER LOOP ===
function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();

// === HANDLE RESIZE ===
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
