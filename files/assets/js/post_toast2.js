function post_toast2(url, button1, button2) {
	document.getElementById('toast-post-error-text').innerText = "Error, please try again later."

	const xhr = new XMLHttpRequest();
	xhr.open("POST", url, true);
	xhr.setRequestHeader('xhr', 'xhr');
	var form = new FormData()
	form.append("formkey", formkey());

	if(typeof data === 'object' && data !== null) {
		for(let k of Object.keys(data)) {
				form.append(k, data[k]);
		}
	}


	form.append("formkey", formkey());
	xhr.withCredentials=true;

	xhr.onload = function() {
		let data
		try {data = JSON.parse(xhr.response)}
		catch(e) {console.log(e)}
		if (xhr.status >= 200 && xhr.status < 300 && data && data["message"]) {
			document.getElementById('toast-post-success-text').innerText = data["message"];
			new bootstrap.Toast(document.getElementById('toast-post-success')).show();

			document.getElementById(button1).classList.toggle("d-none");
			document.getElementById(button2).classList.toggle("d-none");
		
		} else {
			if (data && data["error"]) document.getElementById('toast-post-error-text').innerText = data["error"];
			new bootstrap.Toast(document.getElementById('toast-post-error')).show();
		}
	};

	xhr.send(form);
}