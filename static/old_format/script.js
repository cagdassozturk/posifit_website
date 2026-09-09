const carousel = document.querySelector('.carousel');
const leftBtn = document.querySelector('.left-arrow');
const rightBtn = document.querySelector('.right-arrow');

let scrollPosition = 0;
const cardWidth = 260; // 240px + 20px gap

rightBtn.addEventListener('click', () => {
  scrollPosition += cardWidth;
  carousel.style.transform = `translateX(-${scrollPosition}px)`;
});

leftBtn.addEventListener('click', () => {
  scrollPosition = Math.max(scrollPosition - cardWidth, 0);
  carousel.style.transform = `translateX(-${scrollPosition}px)`;
});
