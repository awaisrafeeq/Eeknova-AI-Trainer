// Simple frontend test script
console.log('Testing frontend setup...');

// Test if we can access the frontend
fetch('http://localhost:3000')
  .then(response => {
    console.log('✅ Frontend is accessible!');
    console.log('Status:', response.status);
    return response.text();
  })
  .then(html => {
    console.log('✅ Frontend loaded successfully');
    console.log('Page length:', html.length, 'characters');
  })
  .catch(error => {
    console.log('❌ Frontend error:', error.message);
  });

// Test auth page
fetch('http://localhost:3000/auth')
  .then(response => {
    console.log('✅ Auth page is accessible!');
    console.log('Status:', response.status);
  })
  .catch(error => {
    console.log('❌ Auth page error:', error.message);
  });

console.log('Frontend test completed!');
