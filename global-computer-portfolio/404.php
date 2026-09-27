<?php
/** Not-found page. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
get_header();
?>
<main id="main-content" class="site-main not-found-page">
	<div class="wrap not-found-page__inner">
		<p class="eyebrow"><span class="eyebrow__rule" aria-hidden="true"></span><?php esc_html_e( '404 · Page not found', 'global-computer-portfolio' ); ?></p>
		<h1><?php esc_html_e( 'This page took a wrong turn.', 'global-computer-portfolio' ); ?></h1>
		<p><?php esc_html_e( 'Try the personal portfolio or visit the business profile instead.', 'global-computer-portfolio' ); ?></p>
		<div class="hero-actions">
			<a class="button button--ink" href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php esc_html_e( 'Back to the portfolio', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
			<a class="text-link" href="<?php echo esc_url( gcp_business_url() ); ?>"><?php echo esc_html( gcp_setting( 'business_name', 'Global Computer & Technology' ) ); ?><span aria-hidden="true">↗</span></a>
		</div>
	</div>
</main>
<?php get_footer(); ?>
