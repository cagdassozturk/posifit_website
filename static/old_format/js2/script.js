import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js';

// Scene & Canvas
const canvas = document.getElementById('c');
const scene = new THREE.Scene();

// Camera
const camera = new THREE.PerspectiveCamera(20, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 0, 6);
scene.add(camera);

// Renderer
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1;
renderer.outputEncoding = THREE.sRGBEncoding;

// Handle resize
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

let model;

new RGBELoader()
  .setPath('model/')
  .load('environment.hdr', function (hdrTexture) {
    hdrTexture.mapping = THREE.EquirectangularReflectionMapping;
    scene.environment = hdrTexture;
    scene.background = null;
    loadModel();
  });

function loadModel() {
  const loader = new GLTFLoader();
  loader.load(
    'model/LEGOFIT_model.glb',
    gltf => {
      model = gltf.scene;
      scene.add(model);

      model.traverse(child => {
        if (child.isMesh && child.material) {
          child.material.metalness = 0.1;
          child.material.roughness = 0.7;
          child.material.needsUpdate = true;
        }
      });

      // Center model
      const box = new THREE.Box3().setFromObject(model);
      const center = box.getCenter(new THREE.Vector3());
      model.position.sub(center);

      // Initial camera setup
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z);
      const fov = camera.fov * (Math.PI / 180);
      const cameraZ = maxDim / (2 * Math.tan(fov / 2));
      camera.position.set(0, 0, cameraZ * 1.5);
      camera.lookAt(0, 0, 0);

      // Start scroll listener after model is ready
      window.addEventListener('scroll', () => {
        const scrollY = window.scrollY || window.pageYOffset;
        const scrollRange = window.innerHeight;
        const progress = Math.min(Math.max(scrollY / scrollRange, 0), 1);
        model.rotation.y = progress * Math.PI * 2;
        model.position.z = -progress * 1.5;
      });
    },
    undefined,
    error => {
      console.error('❌ Failed to load model:', error);
    }
  );
}

// Animate
function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();
