document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('signupForm');
  const referralLink = document.querySelector('.referral-link');
  const referralInput = document.querySelector('.referral-input');
  
  // Handle referral code toggle
  referralLink.addEventListener('click', function(e) {
      e.preventDefault();
      referralInput.style.display = referralInput.style.display === 'none' ? 'block' : 'none';
  });
  
  // Form validation
  form.addEventListener('submit', function(e) {
      e.preventDefault();
      
      const password1 = form.querySelector('input[name="password1"]').value;
      const password2 = form.querySelector('input[name="password2"]').value;
      
      if (password1 !== password2) {
          alert('Passwords do not match!');
          return;
      }
      
      // If validation passes, submit the form
      form.submit();
  });
  
  // Close button functionality
  document.querySelector('.close-btn').addEventListener('click', function() {
      window.history.back();
  });
});