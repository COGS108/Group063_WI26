////////////////////////////////////////////////////
// DESIGNPLUS CONFIG                            //
////////////////////////////////////////////////////
// Legacy
var DT_variables = {
        iframeID: '',
        // Path to the hosted USU Design Tools
        path: 'https://designtools.ciditools.com/',
        templateCourse: '60856',
        // OPTIONAL: Button will be hidden from view until launched using shortcut keys
        hideButton: false,
         // OPTIONAL: Limit by course format
         limitByFormat: false, // Change to true to limit by format
         // adjust the formats as needed. Format must be set for the course and in this array for tools to load
         formatArray: [
            'online',
            'on-campus',
            'blended'
        ],
        // OPTIONAL: Limit tools loading by users role
        limitByRole: false, // set to true to limit to roles in the roleArray
        // adjust roles as needed
        roleArray: [
            'student',
            'teacher',
            'admin'
        ],
        // OPTIONAL: Limit tools to an array of Canvas user IDs
        limitByUser: true, // Change to true to limit by user
        // add users to array (Canvas user ID not SIS user ID)
        userArray: [
            '3594', //Cindy Perez
            '121230', //Stephen Wilcox
            '140133', //Laura Giffin
            '123037', //Nick Mattos
            '111056', //Alan Roper
            '111058', //Laura Rosenzweig
            '1869', //Edual Ruiz
            '192335', //I-Pang Fu
            '207761', //Nicole Manley
            '207677', //Eric Peloza
            '211731', //Mimi Phung
            '12945', //Kayleigh Kumiko Setoda
            '237744', //Markia Herron
	    '182203', //Nigel Johnson
	    '12931', //Victoria Bartlett
	    '9601', //Lisa Gole
	    '103446', //Pathe Seck
	    '9583', //Christopher Cannivino
            '204084', //Rosa Longacre
            '20429', //Ariana Mueller
            '19174', //Shannon O'Donnell
            '292752', //Rachael Pryce

        ]
};

// New
DpPrimary = {
    lms: 'canvas',
    templateCourse: '60856',
    hideButton: false,
    hideLti: false,
    extendedCourse: '', // added in sub-account theme
    sharedCourse: '', // added from localStorage
    courseFormats: [],
    canvasRoles: [],
    canvasUsers: [
	    '3594', //Cindy Perez
            '121230', //Stephen Wilcox
            '140133', //Laura Giffin
            '123037', //Nick Mattos
            '111056', //Alan Roper
            '111058', //Laura Rosenzweig
            '1869', //Edual Ruiz
            '192335', //I-Pang Fu
            '207761', //Nicole Manley
            '207677', //Eric Peloza
            '211731', //Mimi Phung
            '12945', //Kayleigh Kumiko Setoda
            '237744', //Markia Herron
	    '182203', //Nigel Johnson
	    '12931', //Victoria Bartlett
	    '9601', //Lisa Gole
	    '103446', //Pathe Seck
	    '9583', //Christopher Cannivino
            '204084', //Rosa Longacre
            '20429', //Ariana Mueller
            '19174', //Shannon O'Donnell
            '292752', //Rachael Pryce


	],
    canvasCourseIds: [],
    plugins: [],
    excludedModules: [],
    includedModules: [],
    lang: 'en',
    defaultToLegacy: true,
    enableVersionSwitching: true,
    hideSwitching: false,
}

// merge with extended/shared customizations config
DpConfig = { ...DpPrimary, ...(window.DpConfig ?? {}) }

$(function () {
    const uriPrefix = (location.href.includes('.beta.')) ? 'beta.' : '';
    const toolsUri = (DpConfig.toolsUri) ? DpConfig.toolsUri : `https://${uriPrefix}designplus.ciditools.com/`;
    $.getScript(`${toolsUri}js/controller.js`);
});
////////////////////////////////////////////////////
// END DESIGNPLUS CONFIG                        //
////////////////////////////////////////////////////

// Checks if page is dashboard
$(document).ready(function(){
    if (window.location.pathname=='/') {
        $('#DashboardCard_Container').before('<div><p>Additional courses, including those from previous quarters, may be found on your <a href="/courses">All Courses</a> page.</p></div>');
    }});

//Hide Canvas's Course Start Checklist
$(document).ready(function(){

    // Check if page is course homepage
    if (/^\/courses\/[0-9]+$/.test(window.location.pathname)) {
            // Disables the Canvas Course Checklist button
            $('div.course-options a.btn.button-sidebar-wide.wizard_popup_link').remove();}

});


// If the URL has #hash content, and the page has a IMVHKalturaElement div, inject the kaltura player into that div:
let loadKaltura = () => {
    if(document.location.hash.length > 1) {
        let kaltura_elements = document.getElementsByClassName("IMVHKalturaElement");

        if(kaltura_elements.length > 0) {
            let entry_id = document.location.hash.substring(1);

            let hostname = document.location.hostname;
            let kaf = (hostname == "ucsd.test.instructure.com") ? 
                "2323111-3.kaf.kaltura.com" :
                "canvaskaf.ucsd.edu";

            // Make the main window wider
            $("#wrapper").css("max-width", "100%")

            let player = kaltura_elements[0];

            let kaf_url = 'https://' + kaf + '/browseandembed/index/media/entryid/' + entry_id + '/playerSkin/52880582/';

            let iframe_src = 'https://' + hostname + '/courses/' + ENV.COURSE_ID + '/external_tools/retrieve?borderless=1&url=' + kaf_url;

            player.innerHTML = '<p><iframe class="lti-embed" style="width: 100%; aspect-ratio: 16 / 9;" src="' + iframe_src + '" allowfullscreen="allowfullscreen" webkitallowfullscreen="webkitallowfullscreen" mozallowfullscreen="mozallowfullscreen" allow="geolocation *; microphone *; camera *; midi *; encrypted-media *; autoplay *; clipboard-write *; display-capture *"></iframe></p>';
        }
    }
};

// Delay load, since the content of wiki pages does not appear to be available immediately
$(document).ready(() => { setTimeout(loadKaltura, 1000); });