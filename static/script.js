
gsap.registerPlugin(ScrollTrigger);

document.addEventListener('DOMContentLoaded', function () {
  window.addEventListener('scroll', () => {
    const chevron = document.querySelector('.scroll-chevron-pixel-container');
    if (window.scrollY > 1) {
      chevron.classList.add('scroll-chevron-pixel-hidden');
    } else {
      chevron.classList.remove('scroll-chevron-pixel-hidden');
    }
  });
});


gsap.utils.toArray('.left-side .title').forEach(title => {
  gsap.fromTo(title, {
    letterSpacing: '10px',
    opacity: 0,
    x: -300,
    skewX: -65
  }, {
    letterSpacing: '0',
    opacity: 1,
    x: 0,
    skewX: 0,
    duration: 0.7,
    delay: 0.1,
    scrollTrigger: title
  });
});

gsap.utils.toArray('.left-side p').forEach(p => {
  gsap.fromTo(p, {
    opacity: 0,
    x: -150,
    skewX: -30
  }, {
    opacity: 1,
    x: 0,
    skewX: 0,
    duration: 0.7,
    delay: 0.1,
    scrollTrigger: p
  });
});

gsap.utils.toArray('.left-side button').forEach(button => {
  gsap.fromTo(button, {
    opacity: 0,
    x: -100
  }, {
    opacity: 1,
    x: 0,
    duration: 0.7,
    delay: 0.1,
    scrollTrigger: button
  });
});

gsap.utils.toArray('.right-side .title').forEach(title => {
  gsap.fromTo(title, {
    letterSpacing: '10px',
    opacity: 0,
    x: 300,
    skewX: 65
  }, {
    letterSpacing: '0',
    opacity: 1,
    x: 0,
    skewX: 0,
    duration: 0.7,
    delay: 0.1,
    scrollTrigger: title
  });
});

gsap.utils.toArray('.right-side p').forEach(p => {
  gsap.fromTo(p, {
    opacity: 0,
    x: 150,
    skewX: 30
  }, {
    opacity: 1,
    x: 0,
    skewX: 0,
    duration: 0.7,
    delay: 0.1,
    scrollTrigger: p
  });
});

gsap.utils.toArray('.right-side button').forEach(button => {
  gsap.fromTo(button, {
    opacity: 0,
    x: 100
  }, {
    opacity: 1,
    x: 0,
    duration: 0.7,
    
    scrollTrigger: button
  });
});



gsap.registerPlugin(ScrollTrigger);

const isSmallScreen = window.innerWidth < 768;
const moveProps = isSmallScreen ? { y: -50 } : { x: -50 };

gsap.timeline({ delay: 1 })
  .to(".logo-main", {
    ...moveProps,
    duration: 0.6,
    ease: "power2.out"
  })
  .to(".logo-x", {
    opacity: 1,
    duration: 0.6,   // longer duration for smoother fade
    ease: "power3.inOut"  // smoother easing
  }, "-=0.4")
  .to(".logo-second", {
    opacity: 1,
    duration: 0.8,
    ease: "power3.inOut"
  }, "-=0.5");
