document.addEventListener("DOMContentLoaded", function () {
  // Wait for the page to fully load
  window.addEventListener("load", function () {
      // Hide the preloader
      const preloader = document.getElementById("preloader");
      preloader.style.display = "none";

      // Show the main content
      const mainContent = document.getElementById("main-content");
      mainContent.style.display = "block";
  });
});
