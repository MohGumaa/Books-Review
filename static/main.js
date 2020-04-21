document.addEventListener('DOMContentLoaded', () => {
  document.querySelector('#searchForm').onsubmit = (e) => {
    e.preventDefault();
    const searchText = document.querySelector('#searchText').value;
    let output = document.querySelector('#output');

    if (searchText.length > 0){
      // Initialize new request
      const request = new XMLHttpRequest;
      request.open('POST', '/search');

      // Callback function for when request completes
      request.onload = () => {
        // Extract JSON data from request
        const data = JSON.parse(request.responseText);
        let info_book ='';

        // Check result of request
        if(data.success){
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

          document.querySelector('#text-output').outerHTML=
          '<h3>Click on name to get more details!</h3>'
          output.innerHTML = info_book;
          console.log(data.books[0].author)
        } else {
          output.innerHTML = `
          <div class="alert alert-danger" role="alert">
            <em>${data.error}</em>
          </div>
          `;
          console.log('error')
        }
      };

      // Add data to send with request
      const data = new FormData();
      data.append('searchText', searchText);

      // Send request
      request.send(data);

    } else {
      output.innerHTML = `
      <div class="alert alert-danger" role="alert">
        <em>Please Enter Title, Author or ISBN!</em>
      </div>
      `;
    }
  };
});
