<?php
/** Site header. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$person_name = gcp_setting( 'person_name', 'Saidul Islam' );
$business_name = gcp_setting( 'business_name', 'Global Computer & Technology' );
$business_logo = gcp_setting( 'business_logo', '' );
?>
<!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
<?php wp_body_open(); ?>
<a class="skip-link" href="#main-content"><?php esc_html_e( 'Skip to content', 'global-computer-portfolio' ); ?></a>
<header class="site-header">
	<div class="site-header__inner wrap">
		<a class="site-brand" href="<?php echo esc_url( home_url( '/' ) ); ?>" aria-label="<?php echo esc_attr( sprintf( __( '%s — home', 'global-computer-portfolio' ), $person_name ) ); ?>">
			<?php $personal_logo_id = get_theme_mod( 'custom_logo' ); ?>
			<?php if ( $personal_logo_id ) : ?>
				<span class="site-brand__image"><?php echo wp_get_attachment_image( $personal_logo_id, 'full', false, array( 'alt' => $person_name ) ); ?></span>
			<?php else : ?>
				<span class="site-brand__mark" aria-hidden="true"><?php echo esc_html( gcp_initials( $person_name, 'SI' ) ); ?></span>
			<?php endif; ?>
			<span class="site-brand__text">
				<strong><?php echo esc_html( $person_name ); ?></strong>
				<span><?php esc_html_e( 'Portfolio', 'global-computer-portfolio' ); ?></span>
			</span>
		</a>

		<button class="menu-toggle" type="button" aria-controls="primary-navigation" aria-expanded="false">
			<span class="menu-toggle__label"><?php esc_html_e( 'Menu', 'global-computer-portfolio' ); ?></span>
			<span class="menu-toggle__icon" aria-hidden="true"><i></i><i></i></span>
		</button>

		<nav class="primary-nav" id="primary-navigation" aria-label="<?php esc_attr_e( 'Main navigation', 'global-computer-portfolio' ); ?>">
			<?php
			wp_nav_menu( array(
				'theme_location' => 'primary',
				'container'      => false,
				'menu_class'     => 'main-nav__links',
				'fallback_cb'    => 'gcp_primary_menu_fallback',
				'depth'          => 1,
			) );
			?>
		</nav>

		<a class="business-shortcut" href="<?php echo esc_url( gcp_business_url() ); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'Visit %s business profile', 'global-computer-portfolio' ), $business_name ) ); ?>">
			<span class="business-shortcut__logo" aria-hidden="true">
				<?php if ( $business_logo ) : ?>
					<img src="<?php echo esc_url( $business_logo ); ?>" alt="">
				<?php else : ?>
					<span>GCT</span>
				<?php endif; ?>
			</span>
			<span class="business-shortcut__text">
				<small><?php esc_html_e( 'The business', 'global-computer-portfolio' ); ?></small>
				<strong><?php echo esc_html( $business_name ); ?></strong>
			</span>
			<span class="business-shortcut__arrow" aria-hidden="true">↗</span>
		</a>
	</div>
</header>
