<?php
/**
 * Template Name: Global Computer & Technology Business Profile
 * Template Post Type: page
 *
 * Dedicated profile for the computer services business.
 *
 * @package GlobalComputerPortfolio
 */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

$business_name     = gcp_setting( 'business_name', 'Global Computer & Technology' );
$business_owner    = gcp_setting( 'business_owner', 'Saidul Islam' );
$owner_title       = gcp_setting( 'business_owner_title', '' );
$business_intro    = gcp_setting( 'business_intro', 'Alongside digital work, the outlet provides direct, on-site computer support.' );
$business_phone    = gcp_setting( 'business_phone', '+880 1886-915167' );
$business_logo     = gcp_setting( 'business_logo', '' );
$phone_uri         = gcp_tel_uri( $business_phone );
$whatsapp_uri      = gcp_whatsapp_uri( $business_phone );
$physical_services = gcp_setting_lines( 'physical_services', "Personal computer setup\nOperating system and Windows installation\nParts replacement\nTechnical consultancy" );
$digital_services  = gcp_setting_lines( 'digital_services', "Growth & performance marketing (CPA and lead generation)\nSocial media advertising, e-commerce and SEO\nYouTube and social media growth & monetization (digital products, gaming)\nAI agents and automation" );
$market_skill      = gcp_setting( 'market_skill', 'Financial & technical market analyst' );

$legal_information = array(
	__( 'Trade / business license number', 'global-computer-portfolio' ) => gcp_setting( 'license_number', '' ),
	__( 'Issuing authority', 'global-computer-portfolio' )                => gcp_setting( 'license_authority', '' ),
	__( 'Registered business address', 'global-computer-portfolio' )      => gcp_setting( 'registered_address', '' ),
	__( 'Shop address', 'global-computer-portfolio' )                     => gcp_setting( 'shop_address', '' ),
);
$has_legal_information = false;
foreach ( $legal_information as $legal_value ) {
	if ( trim( $legal_value ) ) {
		$has_legal_information = true;
		break;
	}
}
?>
<main id="main-content" class="site-main business-page">
	<section class="business-hero">
		<div class="wrap">
			<div class="breadcrumb"><a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php esc_html_e( 'Personal portfolio', 'global-computer-portfolio' ); ?></a><span aria-hidden="true">/</span><span><?php esc_html_e( 'Business profile', 'global-computer-portfolio' ); ?></span></div>
			<div class="business-hero__grid">
				<div class="business-hero__copy">
					<p class="eyebrow"><span class="eyebrow__rule" aria-hidden="true"></span><?php esc_html_e( 'On-site service + digital expertise', 'global-computer-portfolio' ); ?></p>
					<h1><?php echo esc_html( $business_name ); ?></h1>
					<p class="business-hero__intro"><?php echo esc_html( $business_intro ); ?></p>
					<div class="hero-actions">
						<?php if ( $phone_uri ) : ?>
							<a class="button button--ink" href="<?php echo esc_url( $phone_uri ); ?>"><?php esc_html_e( 'Call the business', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
						<?php endif; ?>
						<?php if ( $whatsapp_uri ) : ?>
							<a class="text-link" href="<?php echo esc_url( $whatsapp_uri ); ?>" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'WhatsApp', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
						<?php endif; ?>
					</div>
				</div>
				<div class="business-brand-panel">
					<div class="business-brand-panel__top"><span><?php esc_html_e( 'BUSINESS PROFILE', 'global-computer-portfolio' ); ?></span><span>01 / 01</span></div>
					<a class="business-brand-panel__mark" href="<?php echo esc_url( gcp_business_url() ); ?>" aria-label="<?php echo esc_attr( $business_name ); ?>">
						<?php if ( $business_logo ) : ?>
							<img src="<?php echo esc_url( $business_logo ); ?>" alt="<?php echo esc_attr( $business_name ); ?>">
						<?php else : ?>
							<span class="business-brand-panel__gct">GCT</span>
							<span class="business-brand-panel__caption"><?php esc_html_e( 'COMPUTER + TECHNOLOGY', 'global-computer-portfolio' ); ?></span>
						<?php endif; ?>
					</a>
					<div class="business-brand-panel__bottom"><span><?php esc_html_e( 'OWNER', 'global-computer-portfolio' ); ?></span><strong><?php echo esc_html( $business_owner ); ?></strong></div>
				</div>
			</div>
		</div>
	</section>

	<section class="section business-services" id="on-site-services">
		<div class="wrap">
			<div class="section-grid">
				<div class="section-label"><span>01</span><span><?php esc_html_e( 'At the outlet', 'global-computer-portfolio' ); ?></span></div>
				<div class="business-service-content">
					<div class="section-heading section-heading--business">
						<h2 class="section-title"><?php esc_html_e( 'On-site & physical computer services', 'global-computer-portfolio' ); ?></h2>
						<p><?php esc_html_e( 'Direct help for personal computers, installations and hardware needs.', 'global-computer-portfolio' ); ?></p>
					</div>
					<?php if ( $physical_services ) : ?>
						<ol class="service-list">
							<?php foreach ( $physical_services as $index => $service ) : ?>
								<li><span class="service-list__number"><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span><span class="service-list__name"><?php echo esc_html( $service ); ?></span><span class="service-list__arrow" aria-hidden="true">↗</span></li>
							<?php endforeach; ?>
						</ol>
					<?php endif; ?>
				</div>
			</div>
		</div>
	</section>

	<section class="section business-digital">
		<div class="wrap">
			<div class="section-grid">
				<div class="section-label"><span>02</span><span><?php esc_html_e( 'Online services', 'global-computer-portfolio' ); ?></span></div>
				<div class="business-service-content">
					<div class="section-heading section-heading--business">
						<h2 class="section-title"><?php esc_html_e( 'Digital growth & technology', 'global-computer-portfolio' ); ?></h2>
						<p><?php esc_html_e( 'Specialist areas offered alongside the outlet’s computer services.', 'global-computer-portfolio' ); ?></p>
					</div>
					<?php if ( $digital_services ) : ?>
						<div class="digital-service-grid">
							<?php foreach ( $digital_services as $index => $service ) : ?>
								<article class="digital-service-card">
									<span class="digital-service-card__number"><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span>
									<h3><?php echo esc_html( $service ); ?></h3>
									<span class="digital-service-card__line" aria-hidden="true"></span>
								</article>
							<?php endforeach; ?>
						</div>
					<?php endif; ?>
					<?php if ( $market_skill ) : ?>
						<div class="market-skill"><span><?php esc_html_e( 'Subcategory / skill', 'global-computer-portfolio' ); ?></span><strong><?php echo esc_html( $market_skill ); ?></strong></div>
					<?php endif; ?>
				</div>
			</div>
		</div>
	</section>

	<section class="owner-contact-section" id="business-contact">
		<div class="wrap owner-contact-card">
			<div class="owner-contact-card__intro">
				<p class="eyebrow eyebrow--light"><span class="eyebrow__rule" aria-hidden="true"></span><?php esc_html_e( 'The person behind the business', 'global-computer-portfolio' ); ?></p>
				<h2><?php echo esc_html( $business_owner ); ?></h2>
				<?php if ( $owner_title ) : ?><p class="owner-contact-card__title"><?php echo esc_html( $owner_title ); ?></p><?php endif; ?>
			</div>
			<div class="owner-contact-card__actions">
				<?php if ( $business_phone ) : ?>
					<span class="owner-contact-card__label"><?php esc_html_e( 'BUSINESS PHONE', 'global-computer-portfolio' ); ?></span>
				<?php endif; ?>
				<?php if ( $phone_uri ) : ?><a class="owner-contact-card__phone" href="<?php echo esc_url( $phone_uri ); ?>"><?php echo esc_html( $business_phone ); ?><span aria-hidden="true">↗</span></a><?php endif; ?>
				<?php if ( $whatsapp_uri ) : ?><a class="button button--paper button--compact" href="<?php echo esc_url( $whatsapp_uri ); ?>" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'Message on WhatsApp', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a><?php endif; ?>
			</div>
		</div>
	</section>

	<?php if ( $has_legal_information ) : ?>
		<section class="section legal-section" id="official-information">
			<div class="wrap section-grid">
				<div class="section-label"><span>03</span><span><?php esc_html_e( 'Official information', 'global-computer-portfolio' ); ?></span></div>
				<div class="legal-information">
					<div class="section-heading section-heading--business">
						<h2 class="section-title"><?php esc_html_e( 'Business details', 'global-computer-portfolio' ); ?></h2>
						<p><?php esc_html_e( 'Official registration and address information.', 'global-computer-portfolio' ); ?></p>
					</div>
					<dl class="legal-list">
						<?php foreach ( $legal_information as $label => $value ) : ?>
							<?php if ( trim( $value ) ) : ?>
								<div class="legal-list__row">
									<dt><?php echo esc_html( $label ); ?></dt>
									<dd><?php echo nl2br( esc_html( $value ) ); ?></dd>
								</div>
							<?php endif; ?>
						<?php endforeach; ?>
					</dl>
				</div>
			</div>
		</section>
	<?php endif; ?>

	<?php
	while ( have_posts() ) :
		the_post();
		$page_content = trim( wp_strip_all_tags( get_the_content() ) );
		if ( $page_content ) :
			?>
			<section class="section business-page-editor-content">
				<div class="wrap section-grid">
					<div class="section-label"><span><?php echo esc_html( $has_legal_information ? '04' : '03' ); ?></span><span><?php esc_html_e( 'More information', 'global-computer-portfolio' ); ?></span></div>
					<div class="entry-content"><?php the_content(); ?></div>
				</div>
			</section>
			<?php
		endif;
	endwhile;
	?>

	<section class="business-return">
		<div class="wrap business-return__inner">
			<p><?php esc_html_e( 'Back to the personal portfolio', 'global-computer-portfolio' ); ?></p>
			<a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php echo esc_html( gcp_setting( 'person_name', 'Saidul Islam' ) ); ?><span aria-hidden="true">↗</span></a>
		</div>
	</section>
</main>
<?php get_footer(); ?>
