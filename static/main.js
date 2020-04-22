document.addEventListener('DOMContentLoaded', () => {

  let searchText = document.querySelector('#searchText');
  const loader = document.querySelector(".loader");
  const output = document.querySelector("#output");

  // When form is submit create xml requests
  document.querySelector('#searchForm').onsubmit = (e) => {
    e.preventDefault();

    // Check if user Enter input then create xml or display message
    if (searchText.value.length > 0) {

      // Clear everything in output
      output.innerHTML = '';
      output.style.opacity = 0;

      // Display loader
      loader.style.display = "block";
      loader.style.opacity = 1;

      // Create XMLHttpRequest to search Route
      findBooks(searchText.value, loader, output);
    } else {
      output.innerHTML =
      '<div id="output" class="alert alert-danger" role="alert"><em>Please Enter Title, Author or ISBN!</em></div>';
    }
  };
});


// Function to find books
function findBooks(searchText, loader, output) {

  // Initialize new request
  const request = new XMLHttpRequest;
  request.open('POST', '/search');

  // Callback function for when request completes
  request.onload = () => {
    // Extract JSON data from request
    const data = JSON.parse(request.responseText);

    // Check result of request and display in html
    if(data.success) {
      let info_book ='';
      data.books.forEach((book) => {
        info_book +=`
          <div class="col-md-6 col-lg-3 mt-3">
            <div class="book_info">
              <h4><a href="/bookpage/${book.isbn}">${book.title}</a></h4>
              <div class="bg-dark text-light">By: <strong>${book.author}</strong></div>
            </div>
          </div>
          `;
      });
      setTimeout(() => {
        loader.style.opacity = 0;
        loader.style.display = "none";
        output.innerHTML = info_book;
        setTimeout(() => (output.style.opacity = 1), 50);
        searchText.value = '';
        console.log(searchText);

      }, 100);
      console.log(data);
    } else {
      const error =
      `<div class="alert alert-danger" role="alert" style="width:100%">
        ${data.error}
      </div>`;
      output.innerHTML = error;
      console.log('error')
    }
  }



  // Add data to send with request
  const data = new FormData();
  data.append('searchText', searchText);

  // Send request
  request.send(data);
}
