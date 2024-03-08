
$(document).ready(function(){
    if (typeof Cookies.get('spm_access') === 'undefined'){
        // $('#body').append('<div id="disclaimerDiv" class="grid flex place-items-center">');
        // $('#topbarRight').append('<div id="loginDiv" class="grid h-1/2 place-items-center">');
        $('#body').append('<h1 id="disclaimer" class="text-white font-bold pl-5 pt-10">Welcome to SPLAM. Logging in grants us access to your account. We will store access credentials that will allow us to create and update your playlists in the background.</h1>');
        $('#topbarRight').append('<button id="loginButton" class="bg-[#1ed760] hover:bg-[#1ed910] text-black font-bold py-2 px-4 rounded-full">Login with Spotify</button>');
    } else {
        $('#topbarRight').append('<button id="logoutButton" class="bg-[#1ed760] hover:bg-[#1ed910] text-black font-bold py-2 px-4 rounded-full">Logout</button>');
        // fetch /spotify/?unmanaged. store json of user playlists, create grid of selectable rectangles. make sure liked songs and release radar are first.
        // fetch /genres.
        // create a new empty grid and a + button bellow it that adds a new item to the grid. each rectangle: Playlist Name: [   ]  genres: [    ]
        // add Create button that posts to /plm with all the above data.
       }
    $('#loginButton').click(function() {
        window.location.href = '/login';
        return false;
    });
    $('#logoutButton').click(function() {
        Cookies.remove('spm_access', { path: '/' });
        Cookies.remove('spm_access', { path: '/' });
        window.location.href = '/';
        return false;
    });

});
