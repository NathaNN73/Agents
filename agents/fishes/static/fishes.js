async function fetchFishes() {
	const response = await fetch("/fishes");
	if (!response.ok) {
		throw new Error(`HTTP error! Status: ${response.status}`);
	}
	return response.json();
}

function drawFish(ctx, fish) {
	ctx.fillStyle = `#${fish.color.toString(16).padStart(6, "0")}ff`;
	ctx.strokeStyle = "#000";
	ctx.beginPath();
	ctx.arc(
		fish.x,
		fish.y,
		fish.size,
		0,
		2 * Math.PI,
	);
	ctx.fill();
	ctx.stroke();
}

!(() => {
	const canvas = document.getElementById("elCanvas");
	const ctx = canvas.getContext("2d");
	if (!ctx) {
		console.error("2D context not supported/available.");
		return;
	}
	canvas.width = 1500;
	canvas.height = 900;

	const intervalId = setInterval(async () => {
		const fishes = await fetchFishes();
		canvas.width = canvas.width;
		//ctx.clearRect(0, 0, canvas.width, canvas.height);
		for (const fish of fishes) {
			drawFish(ctx, fish);
		}
	}, 200);

	console.log(`Canvas drawing started with interval ID: ${intervalId}.`);
})();
