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
            <div class="col-12 col-sm-6 col-md-3 col-lg-2 mt-3">
              <div class="card">
                <h4>${book.title}</h4>
                <div class="bg-dark">By:<a href="/bookpage/${book.isbn}" class="text-light">${book.author}</a></div>
              </div>
            </div>
            `;
          });

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
