function saveUser(userData) {

    localStorage.setItem(
        STORAGE_KEYS.USER,
        JSON.stringify(userData)
    );
}

function getCurrentUser() {

    return JSON.parse(
        localStorage.getItem(STORAGE_KEYS.USER)
    );
}

function logout() {

    auth.signOut()
        .then(() => {

            localStorage.removeItem(
                STORAGE_KEYS.USER
            );

            window.location.href =
                ROUTES.INDEX;
        })
        .catch((error) => {
            console.error(error);
        });
}

function requireAuth() {

    const user = getCurrentUser();

    if (!user) {

        window.location.href =
            ROUTES.INDEX;
    }
}

function redirectIfAuthenticated() {

    const user = getCurrentUser();

    if (user) {

        const profile = getProfile();

        if (profile) {

            window.location.href =
                ROUTES.HOME;

        } else {

            window.location.href =
                ROUTES.PROFILE;
        }
    }
}

async function signInWithGoogle() {

    try {

        const result =
            await auth.signInWithPopup(
                googleProvider
            );

        const user = result.user;

        const userData = {
            uid: user.uid,
            name: user.displayName,
            email: user.email,
            photo: user.photoURL
        };

        saveUser(userData);

        const profile = getProfile();

        if (profile) {

            window.location.href =
                ROUTES.HOME;

        } else {

            window.location.href =
                ROUTES.PROFILE;
        }

    } catch (error) {

        console.error(error);

        showMessage(
            "Google Sign In Failed"
        );
    }
}

auth.onAuthStateChanged((user) => {

    if (user) {

        saveUser({
            uid: user.uid,
            name: user.displayName,
            email: user.email,
            photo: user.photoURL
        });
    }
});