const StatusTable = $('#health-check>tbody');
const ProgressBar = $('#health-check-progress');

/**
 * Render health checks results
 * @param response - http response of health check
 */
function renderStatusTable(response) {
  ProgressBar.remove();
  for (let key in response) {
    if (response.hasOwnProperty(key)) {
      let StatusClass = (response[key]['status'] === "OK") ? "bg-success":"bg-danger";
      StatusTable.append(` \
        <tr> \
        <td class="w-25">${response[key]['description']}</td> \
        <td class="${StatusClass} text-center w-75">${response[key]['status']}</td> \
        </tr> \
      `);
    }
  }
}

/**
 * Render failed request
 * @param response - Failed http response of health check
 */
function renderError(response) {
  ProgressBar.remove();
  let error;
  if (response.status === 500) {
    error = response.statusText;
  }
  else {
    error = JSON.stringify(response.responseJSON, null, 4);
  }
  StatusTable.append(`<tr><td colspan="2"><code style="white-space:pre">${error}</code></td></tr>`);
}

/**
 * Perform request to make health check of entire app and render results
 * @param url - Url of health check api endpoint
 */
function renderPerformHealthCheck(url) {
  $.ajax({
    url: url,
    type: 'GET',
    dataType: 'json',
    success: response => {
      renderStatusTable(response)
    },
    error: response => {
      renderError(response)
    }
  });
}
