<?php
/**
 * Theme functions for Global Computer Portfolio.
 *
 * @package GlobalComputerPortfolio
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/** Theme setup. */
function gcp_setup() {
	load_theme_textdomain( 'global-computer-portfolio', get_template_directory() . '/languages' );

	add_theme_support( 'title-tag' );
	add_theme_support( 'automatic-feed-links' );
	add_theme_support( 'post-thumbnails' );
	add_theme_support( 'custom-logo', array(
		'height'      => 72,
		'width'       => 220,
		'flex-height' => true,
		'flex-width'  => true,
	) );
	add_theme_support( 'html5', array( 'search-form', 'comment-form', 'comment-list', 'gallery', 'caption', 'style', 'script' ) );

	register_nav_menus( array(
		'primary' => __( 'Primary navigation', 'global-computer-portfolio' ),
		'footer'  => __( 'Footer navigation', 'global-computer-portfolio' ),
	) );
}
add_action( 'after_setup_theme', 'gcp_setup' );

/** Enqueue the theme's local assets. */
function gcp_enqueue_assets() {
	$theme = wp_get_theme();
	$version = $theme->get( 'Version' ) ? $theme->get( 'Version' ) : '1.0.0';

	wp_enqueue_style(
		'gcp-theme',
		get_stylesheet_uri(),
		array(),
		$version
	);
	wp_enqueue_style(
		'gcp-main',
		get_theme_file_uri( '/assets/css/main.css' ),
		array( 'gcp-theme' ),
		$version
	);

	wp_enqueue_script(
		'gcp-main',
		get_theme_file_uri( '/assets/js/main.js' ),
		array(),
		$version,
		true
	);
}
add_action( 'wp_enqueue_scripts', 'gcp_enqueue_assets' );

/** Read a theme setting with a safe fallback. */
function gcp_setting( $key, $default = '' ) {
	$value = get_theme_mod( 'gcp_' . $key, $default );
	return is_string( $value ) ? $value : $default;
}

/** Convert a multiline setting into clean, non-empty lines. */
function gcp_setting_lines( $key, $default = '' ) {
	$value = gcp_setting( $key, $default );
	if ( ! is_string( $value ) || '' === trim( $value ) ) {
		return array();
	}

	$lines = preg_split( '/\r\n|\r|\n/', $value );
	$lines = array_map( 'trim', $lines );
	$lines = array_filter( $lines, 'strlen' );

	return array_values( $lines );
}

/** Return the personal section URL on any page. */
function gcp_section_url( $section ) {
	$section = sanitize_title( $section );
	if ( is_front_page() ) {
		return '#' . $section;
	}
	return home_url( '/#' . $section );
}

/** Resolve the business profile permalink. */
function gcp_business_url() {
	$page = get_page_by_path( 'global-computer-technology', OBJECT, 'page' );
	if ( $page instanceof WP_Post && 'publish' === $page->post_status ) {
		return get_permalink( $page );
	}
	return home_url( '/global-computer-technology/' );
}

/** Make a telephone URI from a displayed phone number. */
function gcp_tel_uri( $phone ) {
	$phone = preg_replace( '/[^0-9+]/', '', (string) $phone );
	return $phone ? 'tel:' . $phone : '';
}

/** Make a WhatsApp URL from a displayed phone number. */
function gcp_whatsapp_uri( $phone ) {
	$digits = preg_replace( '/[^0-9]/', '', (string) $phone );
	return $digits ? 'https://wa.me/' . $digits : '';
}

/** Build a simple initials fallback for uploaded portraits/logos. */
function gcp_initials( $name, $fallback = 'SI' ) {
	$name = trim( (string) $name );
	if ( '' === $name ) {
		return $fallback;
	}

	$parts = preg_split( '/\s+/', $name );
	$initials = '';
	foreach ( array_slice( $parts, 0, 2 ) as $part ) {
		$initials .= strtoupper( substr( $part, 0, 1 ) );
	}

	return $initials ? $initials : $fallback;
}

/** Register the small, optional work portfolio used on the homepage. */
function gcp_register_project_type() {
	$labels = array(
		'name'                  => __( 'Portfolio projects', 'global-computer-portfolio' ),
		'singular_name'         => __( 'Portfolio project', 'global-computer-portfolio' ),
		'add_new_item'          => __( 'Add portfolio project', 'global-computer-portfolio' ),
		'edit_item'             => __( 'Edit portfolio project', 'global-computer-portfolio' ),
		'new_item'              => __( 'New portfolio project', 'global-computer-portfolio' ),
		'view_item'             => __( 'View portfolio project', 'global-computer-portfolio' ),
		'search_items'          => __( 'Search portfolio projects', 'global-computer-portfolio' ),
		'not_found'             => __( 'No projects found.', 'global-computer-portfolio' ),
		'not_found_in_trash'    => __( 'No projects found in Trash.', 'global-computer-portfolio' ),
		'menu_name'             => __( 'Portfolio Projects', 'global-computer-portfolio' ),
	);

	register_post_type( 'gcp_project', array(
		'labels'             => $labels,
		'public'             => true,
		'publicly_queryable' => true,
		'show_ui'            => true,
		'show_in_rest'       => true,
		'has_archive'        => false,
		'rewrite'            => array( 'slug' => 'project' ),
		'menu_icon'          => 'dashicons-portfolio',
		'supports'           => array( 'title', 'editor', 'excerpt', 'thumbnail' ),
		'menu_position'      => 21,
	) );
}
add_action( 'init', 'gcp_register_project_type' );

/** Add an optional external project link field. */
function gcp_add_project_url_box() {
	add_meta_box(
		'gcp-project-url',
		__( 'Project link (optional)', 'global-computer-portfolio' ),
		'gcp_render_project_url_box',
		'gcp_project',
		'side',
		'default'
	);
}
add_action( 'add_meta_boxes_gcp_project', 'gcp_add_project_url_box' );

/** Render the project URL field. */
function gcp_render_project_url_box( $post ) {
	wp_nonce_field( 'gcp_save_project_url', 'gcp_project_url_nonce' );
	$url = get_post_meta( $post->ID, '_gcp_project_url', true );
	?>
	<p>
		<label for="gcp-project-url-field"><?php esc_html_e( 'If this project has a public link, add it here. Otherwise the card opens its WordPress project page.', 'global-computer-portfolio' ); ?></label>
	</p>
	<input type="url" id="gcp-project-url-field" name="gcp_project_url" value="<?php echo esc_attr( $url ); ?>" class="widefat" placeholder="https://" />
	<?php
}

/** Save the optional project URL safely. */
function gcp_save_project_url( $post_id ) {
	if ( ! isset( $_POST['gcp_project_url_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['gcp_project_url_nonce'] ) ), 'gcp_save_project_url' ) ) {
		return;
	}
	if ( defined( 'DOING_AUTOSAVE' ) && DOING_AUTOSAVE ) {
		return;
	}
	if ( ! current_user_can( 'edit_post', $post_id ) ) {
		return;
	}

	$url = isset( $_POST['gcp_project_url'] ) ? esc_url_raw( wp_unslash( $_POST['gcp_project_url'] ) ) : '';
	if ( $url ) {
		update_post_meta( $post_id, '_gcp_project_url', $url );
	} else {
		delete_post_meta( $post_id, '_gcp_project_url' );
	}
}
add_action( 'save_post_gcp_project', 'gcp_save_project_url' );

/** Create the dedicated business page after activation without duplicating content. */
function gcp_create_business_page() {
	$page = get_page_by_path( 'global-computer-technology', OBJECT, 'page' );

	if ( $page instanceof WP_Post ) {
		$template = get_post_meta( $page->ID, '_wp_page_template', true );
		if ( '' === $template || 'default' === $template ) {
			update_post_meta( $page->ID, '_wp_page_template', 'page-business.php' );
		}
		update_option( 'gcp_business_page_id', (int) $page->ID );
		return;
	}

	$page_id = wp_insert_post( array(
		'post_title'     => __( 'Global Computer & Technology', 'global-computer-portfolio' ),
		'post_name'      => 'global-computer-technology',
		'post_status'    => 'publish',
		'post_type'      => 'page',
		'post_content'   => '',
		'comment_status' => 'closed',
	), true );

	if ( ! is_wp_error( $page_id ) && $page_id ) {
		update_post_meta( $page_id, '_wp_page_template', 'page-business.php' );
		update_option( 'gcp_business_page_id', (int) $page_id );
		flush_rewrite_rules( false );
	}
}
add_action( 'after_switch_theme', 'gcp_create_business_page' );

/** Register editable profile and business details in the Customizer. */
function gcp_customize_register( $wp_customize ) {
	$wp_customize->add_section( 'gcp_personal_profile', array(
		'title'       => __( 'Personal Profile', 'global-computer-portfolio' ),
		'priority'    => 32,
		'description' => __( 'Edit the personal portfolio content. Leave optional contact fields blank to keep them off the public site.', 'global-computer-portfolio' ),
	) );

	$wp_customize->add_section( 'gcp_business_profile', array(
		'title'       => __( 'Business Profile', 'global-computer-portfolio' ),
		'priority'    => 33,
		'description' => __( 'Edit the Global Computer & Technology page. Official license and address fields are hidden publicly until you enter real details.', 'global-computer-portfolio' ),
	) );

	$personal_text_fields = array(
		'person_name' => array(
			'label'   => __( 'Personal display name', 'global-computer-portfolio' ),
			'default' => 'Saidul Islam',
		),
		'person_role' => array(
			'label'   => __( 'Professional title', 'global-computer-portfolio' ),
			'default' => 'Growth & performance marketing · Computer & technology services',
		),
		'hero_headline' => array(
			'label'   => __( 'Homepage headline', 'global-computer-portfolio' ),
			'default' => "Grow online.\nGet the tech right.",
			'type'    => 'textarea',
		),
		'hero_intro' => array(
			'label'   => __( 'Homepage introduction', 'global-computer-portfolio' ),
			'default' => 'I work across performance marketing, social growth and hands-on computer support—bringing online skills and local service together.',
			'type'    => 'textarea',
		),
		'about_text' => array(
			'label'   => __( 'About text', 'global-computer-portfolio' ),
			'default' => 'My work combines practical digital skills with direct computer services: from campaign and lead-generation work to setup, installation and technical advice.',
			'type'    => 'textarea',
		),
		'personal_email' => array(
			'label'       => __( 'Personal email (optional)', 'global-computer-portfolio' ),
			'default'     => '',
			'type'        => 'email',
			'description' => __( 'Only enter an email that belongs to the portfolio owner.', 'global-computer-portfolio' ),
		),
		'personal_whatsapp' => array(
			'label'       => __( 'Personal WhatsApp URL (optional)', 'global-computer-portfolio' ),
			'default'     => '',
			'type'        => 'url',
			'description' => __( 'Leave blank if the business number should only appear on the business profile.', 'global-computer-portfolio' ),
		),
		'facebook_url' => array(
			'label'   => __( 'Facebook profile URL (optional)', 'global-computer-portfolio' ),
			'default' => '',
			'type'    => 'url',
		),
		'youtube_url' => array(
			'label'   => __( 'YouTube profile URL (optional)', 'global-computer-portfolio' ),
			'default' => '',
			'type'    => 'url',
		),
		'instagram_url' => array(
			'label'   => __( 'Instagram profile URL (optional)', 'global-computer-portfolio' ),
			'default' => '',
			'type'    => 'url',
		),
	);

	foreach ( $personal_text_fields as $key => $field ) {
		$setting_id = 'gcp_' . $key;
		$sanitize = isset( $field['type'] ) && 'url' === $field['type'] ? 'esc_url_raw' : ( isset( $field['type'] ) && 'textarea' === $field['type'] ? 'sanitize_textarea_field' : ( isset( $field['type'] ) && 'email' === $field['type'] ? 'sanitize_email' : 'sanitize_text_field' ) );
		$wp_customize->add_setting( $setting_id, array(
			'default'           => $field['default'],
			'sanitize_callback' => $sanitize,
			'transport'         => 'refresh',
		) );
		$control_args = array(
			'label'       => $field['label'],
			'section'     => 'gcp_personal_profile',
			'settings'    => $setting_id,
			'priority'    => 10,
		);
		if ( isset( $field['description'] ) ) {
			$control_args['description'] = $field['description'];
		}
		$control_type = isset( $field['type'] ) ? $field['type'] : 'text';
		if ( 'textarea' === $control_type ) {
			$control_args['type'] = 'textarea';
		} elseif ( 'email' === $control_type || 'url' === $control_type ) {
			$control_args['type'] = $control_type;
		} else {
			$control_args['type'] = 'text';
		}
		$wp_customize->add_control( $setting_id, $control_args );
	}

	$wp_customize->add_setting( 'gcp_personal_photo', array(
		'default'           => '',
		'sanitize_callback' => 'esc_url_raw',
		'transport'         => 'refresh',
	) );
	$wp_customize->add_control( new WP_Customize_Image_Control( $wp_customize, 'gcp_personal_photo', array(
		'label'       => __( 'Personal photo (optional)', 'global-computer-portfolio' ),
		'description' => __( 'A real photo may be uploaded here. If left blank, the site uses a typographic initials treatment.', 'global-computer-portfolio' ),
		'section'     => 'gcp_personal_profile',
		'settings'    => 'gcp_personal_photo',
	) ) );

	$business_fields = array(
		'business_name' => array(
			'label'   => __( 'Business name', 'global-computer-portfolio' ),
			'default' => 'Global Computer & Technology',
			'type'    => 'text',
		),
		'business_owner' => array(
			'label'   => __( 'Business owner', 'global-computer-portfolio' ),
			'default' => 'Saidul Islam',
			'type'    => 'text',
		),
		'business_owner_title' => array(
			'label'   => __( 'Owner title (optional)', 'global-computer-portfolio' ),
			'default' => '',
			'type'    => 'text',
		),
		'business_phone' => array(
			'label'   => __( 'Business phone / WhatsApp', 'global-computer-portfolio' ),
			'default' => '+880 1886-915167',
			'type'    => 'text',
		),
		'business_intro' => array(
			'label'   => __( 'Business introduction', 'global-computer-portfolio' ),
			'default' => 'Alongside digital work, the outlet provides direct, on-site computer support.',
			'type'    => 'textarea',
		),
		'physical_services' => array(
			'label'   => __( 'On-site computer services (one per line)', 'global-computer-portfolio' ),
			'default' => "Personal computer setup\nOperating system and Windows installation\nParts replacement\nTechnical consultancy",
			'type'    => 'textarea',
		),
		'digital_services' => array(
			'label'   => __( 'Digital services and skills (one per line)', 'global-computer-portfolio' ),
			'default' => "Growth & performance marketing (CPA and lead generation)\nSocial media advertising, e-commerce and SEO\nYouTube and social media growth & monetization (digital products, gaming)\nAI agents and automation",
			'type'    => 'textarea',
		),
		'market_skill' => array(
			'label'   => __( 'Subcategory / additional skill', 'global-computer-portfolio' ),
			'default' => 'Financial & technical market analyst',
			'type'    => 'text',
		),
		'license_number' => array(
			'label'       => __( 'Trade / business license number', 'global-computer-portfolio' ),
			'default'     => '',
			'type'        => 'text',
			'description' => __( 'Enter the exact number shown on the real license. This field is hidden publicly while empty.', 'global-computer-portfolio' ),
		),
		'license_authority' => array(
			'label'       => __( 'License issuing authority', 'global-computer-portfolio' ),
			'default'     => '',
			'type'        => 'text',
			'description' => __( 'Enter the authority exactly as it appears on the license. Hidden while empty.', 'global-computer-portfolio' ),
		),
		'registered_address' => array(
			'label'       => __( 'Registered business address', 'global-computer-portfolio' ),
			'default'     => '',
			'type'        => 'textarea',
			'description' => __( 'Use the exact registered address. Hidden while empty; do not publish a guessed address.', 'global-computer-portfolio' ),
		),
		'shop_address' => array(
			'label'       => __( 'Shop address (if different)', 'global-computer-portfolio' ),
			'default'     => '',
			'type'        => 'textarea',
			'description' => __( 'Optional. Enter only the real customer-facing shop address. Hidden while empty.', 'global-computer-portfolio' ),
		),
	);

	foreach ( $business_fields as $key => $field ) {
		$setting_id = 'gcp_' . $key;
		$sanitize = 'textarea' === $field['type'] ? 'sanitize_textarea_field' : 'sanitize_text_field';
		$wp_customize->add_setting( $setting_id, array(
			'default'           => $field['default'],
			'sanitize_callback' => $sanitize,
			'transport'         => 'refresh',
		) );
		$control_args = array(
			'label'    => $field['label'],
			'section'  => 'gcp_business_profile',
			'settings' => $setting_id,
			'priority' => 10,
		);
		if ( isset( $field['description'] ) ) {
			$control_args['description'] = $field['description'];
		}
		if ( 'textarea' === $field['type'] ) {
			$control_args['type'] = 'textarea';
		} else {
			$control_args['type'] = 'text';
		}
		$wp_customize->add_control( $setting_id, $control_args );
	}

	$wp_customize->add_setting( 'gcp_business_logo', array(
		'default'           => '',
		'sanitize_callback' => 'esc_url_raw',
		'transport'         => 'refresh',
	) );
	$wp_customize->add_control( new WP_Customize_Image_Control( $wp_customize, 'gcp_business_logo', array(
		'label'       => __( 'Business logo (optional)', 'global-computer-portfolio' ),
		'description' => __( 'Upload the shop’s real logo. If none is uploaded, the theme uses a simple “GCT” text mark.', 'global-computer-portfolio' ),
		'section'     => 'gcp_business_profile',
		'settings'    => 'gcp_business_logo',
	) ) );
}
add_action( 'customize_register', 'gcp_customize_register' );

/** Set a content width for embeds and editor defaults. */
function gcp_content_width() {
	$GLOBALS['content_width'] = apply_filters( 'gcp_content_width', 780 );
}
add_action( 'after_setup_theme', 'gcp_content_width', 0 );

/** Navigation shown before a custom WordPress menu is assigned. */
function gcp_primary_menu_fallback() {
	?>
	<ul class="main-nav__links">
		<li><a href="<?php echo esc_url( gcp_section_url( 'about' ) ); ?>"><?php esc_html_e( 'About', 'global-computer-portfolio' ); ?></a></li>
		<li><a href="<?php echo esc_url( gcp_section_url( 'expertise' ) ); ?>"><?php esc_html_e( 'Expertise', 'global-computer-portfolio' ); ?></a></li>
		<li><a href="<?php echo esc_url( gcp_section_url( 'contact' ) ); ?>"><?php esc_html_e( 'Contact', 'global-computer-portfolio' ); ?></a></li>
	</ul>
	<?php
}
