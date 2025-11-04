document.addEventListener('DOMContentLoaded', function() {
  // Close button functionality
  document.querySelector('.close-btn').addEventListener('click', function() {
      window.history.back();
  });

  // Google login button
  document.querySelector('.google-btn').addEventListener('click', function() {
      // Add your Google OAuth logic here
      console.log('Google login clicked');
  });
});