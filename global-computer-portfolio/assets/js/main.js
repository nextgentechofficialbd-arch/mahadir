(function () {
	'use strict';

	var toggle = document.querySelector('.menu-toggle');
	var navigation = document.getElementById('primary-navigation');

	if (!toggle || !navigation) {
		return;
	}

	function closeMenu(returnFocus) {
		toggle.setAttribute('aria-expanded', 'false');
		navigation.classList.remove('is-open');
		if (returnFocus) {
			toggle.focus();
		}
	}

	toggle.addEventListener('click', function () {
		var isExpanded = toggle.getAttribute('aria-expanded') === 'true';
		toggle.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
		navigation.classList.toggle('is-open', !isExpanded);

		if (!isExpanded) {
			var firstLink = navigation.querySelector('a');
			if (firstLink) {
				firstLink.focus();
			}
		}
	});

	navigation.addEventListener('click', function (event) {
		if (event.target.closest('a')) {
			closeMenu(false);
		}
	});

	document.addEventListener('keydown', function (event) {
		if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
			closeMenu(true);
		}
	});

	window.addEventListener('resize', function () {
		if (window.innerWidth > 850 && toggle.getAttribute('aria-expanded') === 'true') {
			closeMenu(false);
		}
	});
}());
