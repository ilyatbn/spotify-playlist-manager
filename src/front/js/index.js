async function fetchUserData() {
    // do this once a session, because I don't really wanna overload requests on the BE for playlists.
    if (sessionStorage.hasOwnProperty("managed_spl")) {
        console.log("unmanaged data already loaded")
        return
    }
    fetch("/spotify/?request_source=managed").then(response=>response.text()).then(
        data=>{
            sessionStorage.setItem('managed_spl', data);
        }
    )
    fetch("/spotify/?request_source=unmanaged").then(response=>response.text()).then(
        data=>{
            sessionStorage.setItem('unmanaged_spl', data);
        }
    )
  }

async function loggedOutContent() {
      $('#body').append('<h1 id="disclaimer" class="text-white font-bold pl-5 pt-10">Welcome to SPLAM. Logging in grants us access to your account. We will store access credentials that will allow us to create and update your playlists in the background.</h1>');
      $('#topbarRight').append('<button id="loginButton" class="bg-[#1ed760] hover:bg-[#1ed910] text-black font-bold py-2 px-4 rounded-full">Login with Spotify</button>');
}

async function loggedInContent() {
    // Add menu options
      $('#topbarRight').append('<button id="logoutButton" class="bg-[#1ed760] hover:bg-[#1ed910] text-black font-bold py-2 px-4 rounded-full">Logout</button>');
      $('#topbarCenter').append('<li><a href="#view" class="block py-2 px-3 text-white md:hover:text-[#1ed760]">View Playlists</a></li>');
      $('#topbarCenter').append('<li><a href="#create" class="block py-2 px-3 text-white md:hover:text-[#1ed760]">Create Playlists</a></li>');
      await fetchUserData();
  }

  async function buildSpotifyPlaylists(){
    $('#body').append(`
    <div id="create_view" class="flex flex-col m-auto p-auto">
        <h1 class="flex px-10 pt-6 font-bold text-2xl text-white">Select source playlists</h1>
        <h3 class="flex px-10 pb-4 font-bold text-sm text-gray-400">Note: Currently only available for playlists created by you or for you.</h1>
        <div  id="src_playlists" class="flex overflow-x-scroll pb-10 hide-scroll-bar">
            <div id="spl_items" class="flex flex-nowrap ml-5 mr-5"></div>
        </div>
    </div>
    `)
    let unmanaged_playlists = JSON.parse(sessionStorage.getItem('unmanaged_spl'))
    unmanaged_playlists.forEach(async (spl) => {
        await buildSpl(spl.playlist_id, spl.name, spl.image_url)
    })
  }

  async function buildSpl(spl_id, spl_name, spl_logo){
    $('#spl_items').append(`
    <div id="spl_item_${spl_id}" data-plid="${spl_id}" class="h-80 w-60 px-1 max-w-xs overflow-hidden rounded-lg shadow-md hover:shadow-2xl transition-shadow duration-300 ease-in-out flex flex-col justify-between">
        <img class="transition-all hover:scale-110 duration-700 h-60 w-60" src="${spl_logo}" alt="${spl_id}" />
        <div id="spl_name" class="h-20 flex flex-col justify-center items-center text-white">
            <h2 class="font-bold">${spl_name}</h2>
        </div>
    </div>
    `)
  }

async function menuRouter(refresh=false) {
    if (refresh===true) {
        console.log("page was refreshed")
    } else {
        $("#create_view").remove()
    }
    if (location.hash === "#view") {
      console.log("You're view");
    }
    if (location.hash === "#create") {
        buildSpotifyPlaylists()

        var scrollContainer = document.getElementById("src_playlists");

        scrollContainer.addEventListener("wheel", (evt) => {
            evt.preventDefault();
            scrollContainer.scrollLeft += evt.deltaY;
        });
        $('[id^="spl_item_"]').on( "click", function() {
            if ($(this).hasClass("spl-selected")) {
                $(this).removeClass("spl-selected")
            } else {
                $(this).addClass("spl-selected")
            }
            $(this).children("#spl_name").toggleClass("bg-gradient-to-t from-[#1ed760_5%] to-transparent")
            console.log($(this).attr('spl-selected'))
        })
    }

}

function setMenuEvents(){
    $('#loginButton').click(function() {
        window.location.href = '/login';
        return false;
    });
    $('#logoutButton').click(function() {
        Cookies.remove('spm_access', { path: '/' });
        Cookies.remove('spm_access', { path: '/' });
        window.location.href = '/';
        sessionStorage.clear()
        return false;
    });
    window.addEventListener("hashchange", menuRouter);
}

$(document).ready(async function(){
    if (typeof Cookies.get('spm_access') === 'undefined'){
        await loggedOutContent()
    } else {
        await loggedInContent()
       }
       setMenuEvents()
    menuRouter(refresh=true)
});
