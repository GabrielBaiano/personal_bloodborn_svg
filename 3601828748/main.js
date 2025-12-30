var canvas = document.querySelector("#player-container");

// Buffer for early Wallpaper Engine property calls
var _pendingProperties = null;
var _initReady = false;
var _localApplyUserProperties = null;

// Always-exist listener to catch Wallpaper Engine events early
window.wallpaperPropertyListener = {
    applyUserProperties: function (properties) {
        if (_initReady && typeof _localApplyUserProperties === "function") {
            _localApplyUserProperties(properties);
        } else {
            _pendingProperties = properties;
        }
    }
};

// Auto-load character name from .config.json
fetch("image/.config.json")
    .then(r => r.json())
    .then(cfg => {
        let skeletonFile = cfg.skeleton || "";
        let defaultCharacter = skeletonFile.replace(".skel", "");
        init(defaultCharacter);
    })
    .catch(err => {
        console.error("⚠️ Failed to read .config.json:", err);
        init("c840_00"); // fallback if no config found
    });

function init(defaultCharacter) {
    var defaultAnimation = "idle";
    var onClickAnimation = "action";
    var onNextAnimation = "idle";

    var isClickAnimationPlaying = false;
    var clickCount = 0;
    var clickTimeout;

    var reproductor = new spine41.SpinePlayer("player-container", {
        skelUrl: "image/" + defaultCharacter + ".skel",
        atlasUrl: "image/" + defaultCharacter + ".atlas",
        animation: defaultAnimation,
        showControls: false,
        alpha: true
    });

    function addImage() {
        if (!document.getElementById("nikke-logo")) {
            let logo = document.createElement("img");
            logo.id = "nikke-logo";
            logo.src = "image/logo_nikke.png";
            logo.style.position = "absolute";
            logo.style.top = "50%";
            logo.style.left = "50%";
            logo.style.transform = "translate(-50%, -50%)";
            logo.style.zIndex = "-1";
            logo.style.pointerEvents = "none";
            logo.style.opacity = "1";
            document.body.appendChild(logo);
        }
    }

    // Click behavior with animation fallback
    canvas.addEventListener("click", function () {
        if (!isClickAnimationPlaying) {
            clickCount++;
            isClickAnimationPlaying = true;

            // Always clear tracks so repeated clicks never freeze
            if (reproductor.player && reproductor.player.state) {
                reproductor.player.state.clearTracks();
            }

            reproductor.setAnimation(onClickAnimation, false);
            reproductor.addAnimation(onNextAnimation, false);
            reproductor.addAnimation(defaultAnimation, true);

            setTimeout(() => {
                isClickAnimationPlaying = false;
            }, 3000);

            if (clickCount > 3) {
                // Try to find which overwhelmed animation exists
                var animToPlay = defaultAnimation; // fallback to idle
                
                if (reproductor.skeleton && reproductor.skeleton.data) {
                    // Check for "serious" first
                    if (reproductor.skeleton.data.findAnimation("serious")) {
                        animToPlay = "serious";
                    }
                    // If not, check for "angry"
                    else if (reproductor.skeleton.data.findAnimation("angry")) {
                        animToPlay = "angry";
                    }
                    // If not, check for "sad"
                    else if (reproductor.skeleton.data.findAnimation("sad")) {
                        animToPlay = "sad";
                    }
                    // Otherwise stays as "idle"
                }
                
                reproductor.setAnimation(animToPlay, false);
                reproductor.addAnimation(defaultAnimation, true);
                clickCount = 0;
            }

            clearTimeout(clickTimeout);
            clickTimeout = setTimeout(() => {
                clickCount = 0;
            }, 12000);
        }
    });

    // Handles Wallpaper Engine properties (color + sliders)
    function applyProps(properties) {
        addImage();
        if (!properties) return;

        // Background color
        if (properties.schemecolor && properties.schemecolor.value) {
            var schemeColor = properties.schemecolor.value.split(" ");
            schemeColor = schemeColor.map(c => Math.floor(c * 255));
            document.body.style.backgroundColor =
                `rgb(${schemeColor[0]},${schemeColor[1]},${schemeColor[2]})`;
        }

        // X position
        if (properties.x && typeof properties.x.value !== "undefined") {
            let posX = properties.x.value;
            canvas.style.left = `${posX}vh`;
        } else if (properties.posX && typeof properties.posX.value !== "undefined") {
            let posX = properties.posX.value;
            canvas.style.left = `${posX}vh`;
        }

        // Y position
        if (properties.y && typeof properties.y.value !== "undefined") {
            let posY = properties.y.value;
            canvas.style.top = `${-posY}vh`;
        } else if (properties.posY && typeof properties.posY.value !== "undefined") {
            let posY = properties.posY.value;
            canvas.style.top = `${-posY}vh`;
        }

        // Z scale
        if (properties.z && typeof properties.z.value !== "undefined") {
            let scale = properties.z.value;
            canvas.style.height = `${scale * 20}vh`;
        } else if (properties.size && typeof properties.size.value !== "undefined") {
            let scale = properties.size.value;
            canvas.style.height = `${scale * 20}vh`;
        }
    }

    // Register local listener for later property updates
    _localApplyUserProperties = applyProps;
    _initReady = true;

    // Apply any properties Wallpaper Engine already sent
    if (_pendingProperties) {
        try {
            applyProps(_pendingProperties);
        } finally {
            _pendingProperties = null;
        }
    }

    // Compatibility: ensure the listener continues working
    window.wallpaperPropertyListener.applyUserProperties = function (properties) {
        applyProps(properties);
    };
}