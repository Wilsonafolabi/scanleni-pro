import './styles/main.css';
import { initApp } from './app';

document.addEventListener('DOMContentLoaded', () => {
  initApp();
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    const html = document.documentElement;
    html.setAttribute('data-bs-theme', html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark');
  });
});