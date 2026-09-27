<?php
/** Site footer. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$person_name = gcp_setting( 'person_name', 'Saidul Islam' );
$business_name = gcp_setting( 'business_name', 'Global Computer & Technology' );
$business_phone = gcp_setting( 'business_phone', '+880 1886-915167' );
$phone_uri = gcp_tel_uri( $business_phone );
$whatsapp_uri = gcp_whatsapp_uri( $business_phone );
?>
<footer class="site-footer">
	<div class="wrap site-footer__top">
		<div class="site-footer__identity">
			<a class="site-footer__name" href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php echo esc_html( $person_name ); ?></a>
			<p><?php esc_html_e( 'Digital growth and practical computer support.', 'global-computer-portfolio' ); ?></p>
		</div>
		<div class="site-footer__links">
			<a href="<?php echo esc_url( gcp_section_url( 'expertise' ) ); ?>"><?php esc_html_e( 'Expertise', 'global-computer-portfolio' ); ?></a>
			<a href="<?php echo esc_url( gcp_business_url() ); ?>"><?php echo esc_html( $business_name ); ?></a>
			<?php if ( $phone_uri ) : ?>
				<a href="<?php echo esc_url( $phone_uri ); ?>"><?php esc_html_e( 'Business line', 'global-computer-portfolio' ); ?> · <?php echo esc_html( $business_phone ); ?></a>
			<?php endif; ?>
		</div>
	</div>
	<div class="wrap site-footer__bottom">
		<span>&copy; <?php echo esc_html( wp_date( 'Y' ) ); ?> <?php echo esc_html( $person_name ); ?></span>
		<?php if ( $whatsapp_uri ) : ?>
			<a class="site-footer__contact" href="<?php echo esc_url( $whatsapp_uri ); ?>" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'WhatsApp the business', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
		<?php endif; ?>
	</div>
</footer>
<?php wp_footer(); ?>
</body>
</html>
