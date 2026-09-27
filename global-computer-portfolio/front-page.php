<?php
/** Homepage portfolio. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();

$person_name    = gcp_setting( 'person_name', 'Saidul Islam' );
$person_role    = gcp_setting( 'person_role', 'Growth & performance marketing · Computer & technology services' );
$headline       = gcp_setting( 'hero_headline', "Grow online.\nGet the tech right." );
$hero_intro     = gcp_setting( 'hero_intro', 'I work across performance marketing, social growth and hands-on computer support—bringing online skills and local service together.' );
$about_text     = gcp_setting( 'about_text', 'My work combines practical digital skills with direct computer services: from campaign and lead-generation work to setup, installation and technical advice.' );
$portrait       = gcp_setting( 'personal_photo', '' );
$business_name  = gcp_setting( 'business_name', 'Global Computer & Technology' );
$business_logo  = gcp_setting( 'business_logo', '' );
$business_intro = gcp_setting( 'business_intro', 'Alongside digital work, the outlet provides direct, on-site computer support.' );
$business_phone = gcp_setting( 'business_phone', '+880 1886-915167' );
$phone_uri      = gcp_tel_uri( $business_phone );
$whatsapp_uri   = gcp_whatsapp_uri( $business_phone );
$digital_items  = gcp_setting_lines( 'digital_services', "Growth & performance marketing (CPA and lead generation)\nSocial media advertising, e-commerce and SEO\nYouTube and social media growth & monetization (digital products, gaming)\nAI agents and automation" );
$market_skill   = gcp_setting( 'market_skill', 'Financial & technical market analyst' );
$personal_whatsapp = gcp_setting( 'personal_whatsapp', '' );
$social_profiles = array(
	'Facebook'  => gcp_setting( 'facebook_url', '' ),
	'YouTube'   => gcp_setting( 'youtube_url', '' ),
	'Instagram' => gcp_setting( 'instagram_url', '' ),
);
?>
<main id="main-content" class="site-main">
	<section class="hero-section">
		<div class="wrap hero-layout">
			<div class="hero-copy">
				<p class="eyebrow"><span class="eyebrow__rule" aria-hidden="true"></span><?php echo esc_html( $person_role ); ?></p>
				<h1 class="hero-title"><?php echo esc_html( $headline ); ?></h1>
				<p class="hero-intro"><?php echo esc_html( $hero_intro ); ?></p>
				<div class="hero-actions">
					<a class="button button--ink" href="#expertise"><?php esc_html_e( 'Explore my work', 'global-computer-portfolio' ); ?><span aria-hidden="true">↓</span></a>
					<a class="text-link" href="<?php echo esc_url( gcp_business_url() ); ?>"><?php esc_html_e( 'Visit the business', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
				</div>
				<p class="hero-byline"><span class="hero-byline__dot" aria-hidden="true"></span><?php echo esc_html( $person_name ); ?> <span class="hero-byline__divider">/</span> <?php esc_html_e( 'Digital & on-site services', 'global-computer-portfolio' ); ?></p>
			</div>

			<div class="hero-board" aria-label="<?php esc_attr_e( 'The two areas of work: online services and on-site computer support', 'global-computer-portfolio' ); ?>">
				<div class="hero-board__topline">
					<span><?php esc_html_e( 'A practical mix', 'global-computer-portfolio' ); ?></span>
					<span class="hero-board__index">01—02</span>
				</div>
				<?php if ( $portrait ) : ?>
					<div class="hero-board__portrait">
						<img src="<?php echo esc_url( $portrait ); ?>" alt="<?php echo esc_attr( $person_name ); ?>">
					</div>
				<?php else : ?>
					<div class="hero-board__monogram" aria-hidden="true"><?php echo esc_html( gcp_initials( $person_name, 'SI' ) ); ?></div>
				<?php endif; ?>
				<div class="hero-board__rows">
					<div class="hero-board__row">
						<span class="hero-board__number">01</span>
						<div><strong><?php esc_html_e( 'Online', 'global-computer-portfolio' ); ?></strong><small><?php esc_html_e( 'Growth · social · automation', 'global-computer-portfolio' ); ?></small></div>
						<span class="hero-board__arrow" aria-hidden="true">↗</span>
					</div>
					<div class="hero-board__row">
						<span class="hero-board__number">02</span>
						<div><strong><?php esc_html_e( 'On-site', 'global-computer-portfolio' ); ?></strong><small><?php esc_html_e( 'Setup · installation · advice', 'global-computer-portfolio' ); ?></small></div>
						<span class="hero-board__arrow" aria-hidden="true">↗</span>
					</div>
				</div>
				<div class="hero-board__foot"><span><?php esc_html_e( 'MARKETING', 'global-computer-portfolio' ); ?></span><span><?php esc_html_e( 'COMPUTER SERVICE', 'global-computer-portfolio' ); ?></span></div>
			</div>
		</div>
		<div class="hero-section__edge" aria-hidden="true"></div>
	</section>

	<section class="section about-section" id="about">
		<div class="wrap section-grid">
			<div class="section-label"><span>01</span><span><?php esc_html_e( 'About', 'global-computer-portfolio' ); ?></span></div>
			<div class="about-content">
				<h2 class="section-title"><?php esc_html_e( 'One person, working across the screen and the shop floor.', 'global-computer-portfolio' ); ?></h2>
				<div class="about-copy">
					<p><?php echo esc_html( $about_text ); ?></p>
					<a class="text-link text-link--underlined" href="<?php echo esc_url( gcp_business_url() ); ?>"><?php esc_html_e( 'More about Global Computer & Technology', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
				</div>
			</div>
		</div>
	</section>

	<section class="section expertise-section" id="expertise">
		<div class="wrap">
			<div class="section-heading section-heading--split">
				<div>
					<div class="section-label"><span>02</span><span><?php esc_html_e( 'Areas of expertise', 'global-computer-portfolio' ); ?></span></div>
					<h2 class="section-title"><?php esc_html_e( 'Work that helps businesses reach, grow and keep moving.', 'global-computer-portfolio' ); ?></h2>
				</div>
				<p class="section-heading__aside"><?php esc_html_e( 'Digital growth skills and practical technology support, shown separately so it is easy to find the right service.', 'global-computer-portfolio' ); ?></p>
			</div>

			<div class="expertise-list">
				<?php if ( $digital_items ) : ?>
					<?php foreach ( $digital_items as $index => $item ) : ?>
						<article class="expertise-row">
							<span class="expertise-row__number"><?php echo esc_html( sprintf( '%02d', $index + 1 ) ); ?></span>
							<h3><?php echo esc_html( $item ); ?></h3>
							<span class="expertise-row__mark" aria-hidden="true">↗</span>
						</article>
					<?php endforeach; ?>
				<?php endif; ?>
			</div>

			<?php if ( $market_skill ) : ?>
				<div class="skill-note">
					<span class="skill-note__label"><?php esc_html_e( 'Additional skill', 'global-computer-portfolio' ); ?></span>
					<span><?php echo esc_html( $market_skill ); ?></span>
				</div>
			<?php endif; ?>
		</div>
	</section>

	<?php
	$projects = new WP_Query( array(
		'post_type'           => 'gcp_project',
		'post_status'         => 'publish',
		'posts_per_page'      => 3,
		'ignore_sticky_posts' => true,
	) );
	$has_projects = (int) $projects->post_count > 0;
	if ( $has_projects ) :
		?>
		<section class="section projects-section" id="projects">
			<div class="wrap">
				<div class="section-heading section-heading--split">
					<div>
						<div class="section-label"><span>03</span><span><?php esc_html_e( 'Selected work', 'global-computer-portfolio' ); ?></span></div>
						<h2 class="section-title"><?php esc_html_e( 'Projects and practical work.', 'global-computer-portfolio' ); ?></h2>
					</div>
					<p class="section-heading__aside"><?php esc_html_e( 'A small selection of work added by the site owner.', 'global-computer-portfolio' ); ?></p>
				</div>
				<div class="project-grid">
					<?php
					$project_index = 0;
					while ( $projects->have_posts() ) :
						$projects->the_post();
						$project_index++;
						$project_url = get_post_meta( get_the_ID(), '_gcp_project_url', true );
						$project_link = $project_url ? $project_url : get_permalink();
						?>
						<article class="project-card">
							<a class="project-card__image" href="<?php echo esc_url( $project_link ); ?>"<?php echo $project_url ? ' target="_blank" rel="noopener noreferrer"' : ''; ?>>
								<?php if ( has_post_thumbnail() ) : ?>
									<?php the_post_thumbnail( 'large', array( 'alt' => the_title_attribute( array( 'echo' => false ) ) ) ); ?>
								<?php else : ?>
									<span class="project-card__fallback" aria-hidden="true"><?php echo esc_html( sprintf( '%02d', $project_index ) ); ?></span>
								<?php endif; ?>
							</a>
							<div class="project-card__body">
								<div>
									<span class="project-card__meta"><?php esc_html_e( 'Project', 'global-computer-portfolio' ); ?> <?php echo esc_html( sprintf( '%02d', $project_index ) ); ?></span>
									<h3><a href="<?php echo esc_url( $project_link ); ?>"<?php echo $project_url ? ' target="_blank" rel="noopener noreferrer"' : ''; ?>><?php the_title(); ?></a></h3>
									<?php if ( has_excerpt() ) : ?><p><?php echo esc_html( get_the_excerpt() ); ?></p><?php endif; ?>
								</div>
								<span class="project-card__arrow" aria-hidden="true">↗</span>
							</div>
						</article>
					<?php endwhile; ?>
				</div>
			</div>
		</section>
		<?php
	endif;
	wp_reset_postdata();
	?>

	<section class="business-feature" aria-labelledby="business-feature-title">
		<div class="wrap business-feature__inner">
			<div class="business-feature__copy">
				<div class="business-feature__eyebrow"><span class="business-feature__tick" aria-hidden="true"></span><?php esc_html_e( 'A separate place for the business', 'global-computer-portfolio' ); ?></div>
				<h2 id="business-feature-title"><?php echo esc_html( $business_name ); ?></h2>
				<p><?php echo esc_html( $business_intro ); ?></p>
				<a class="button button--paper" href="<?php echo esc_url( gcp_business_url() ); ?>"><?php esc_html_e( 'View business profile', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
			</div>
			<a class="business-feature__seal" href="<?php echo esc_url( gcp_business_url() ); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'Visit %s business profile', 'global-computer-portfolio' ), $business_name ) ); ?>">
				<?php if ( $business_logo ) : ?>
					<img src="<?php echo esc_url( $business_logo ); ?>" alt="<?php echo esc_attr( $business_name ); ?>">
				<?php else : ?>
					<span class="business-seal__letters">GCT</span>
					<span class="business-seal__caption"><?php esc_html_e( 'COMPUTER + TECHNOLOGY', 'global-computer-portfolio' ); ?></span>
				<?php endif; ?>
			</a>
			<div class="business-feature__side">
				<span><?php esc_html_e( 'ON-SITE COMPUTER SERVICE', 'global-computer-portfolio' ); ?></span>
				<p><?php esc_html_e( 'Setup, installation, parts replacement and technical advice.', 'global-computer-portfolio' ); ?></p>
				<?php if ( $phone_uri && $business_phone ) : ?>
					<a href="<?php echo esc_url( $phone_uri ); ?>"><?php echo esc_html( $business_phone ); ?><span aria-hidden="true">↗</span></a>
				<?php endif; ?>
				<?php if ( $whatsapp_uri ) : ?>
					<a class="business-feature__whatsapp" href="<?php echo esc_url( $whatsapp_uri ); ?>" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'WhatsApp', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
				<?php endif; ?>
			</div>
		</div>
	</section>

	<section class="section contact-section" id="contact">
		<div class="wrap contact-section__inner">
			<div class="section-label"><span><?php echo esc_html( $has_projects ? '04' : '03' ); ?></span><span><?php esc_html_e( 'Get in touch', 'global-computer-portfolio' ); ?></span></div>
			<div class="contact-section__content">
				<h2 class="section-title"><?php esc_html_e( 'Have a project or need computer support?', 'global-computer-portfolio' ); ?></h2>
				<p><?php esc_html_e( 'For computer services, reach Global Computer & Technology directly. Personal contact details can be added by the site owner when confirmed.', 'global-computer-portfolio' ); ?></p>
				<div class="contact-actions">
					<a class="button button--ink" href="<?php echo esc_url( gcp_business_url() ); ?>"><?php esc_html_e( 'Contact the business', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
					<?php $personal_email = gcp_setting( 'personal_email', '' ); ?>
					<?php if ( $personal_email ) : ?>
						<a class="text-link" href="mailto:<?php echo esc_attr( antispambot( $personal_email ) ); ?>"><?php echo esc_html( antispambot( $personal_email ) ); ?><span aria-hidden="true">↗</span></a>
					<?php endif; ?>
					<?php if ( $personal_whatsapp ) : ?>
						<a class="text-link" href="<?php echo esc_url( $personal_whatsapp ); ?>" target="_blank" rel="noopener noreferrer"><?php esc_html_e( 'Personal WhatsApp', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
					<?php endif; ?>
				</div>
				<?php $active_social_profiles = array_filter( $social_profiles ); ?>
				<?php if ( $active_social_profiles ) : ?>
					<nav class="contact-socials" aria-label="<?php esc_attr_e( 'Social profiles', 'global-computer-portfolio' ); ?>">
						<span><?php esc_html_e( 'Elsewhere', 'global-computer-portfolio' ); ?></span>
						<?php foreach ( $active_social_profiles as $profile_name => $profile_url ) : ?>
							<a href="<?php echo esc_url( $profile_url ); ?>" target="_blank" rel="noopener noreferrer"><?php echo esc_html( $profile_name ); ?><span aria-hidden="true">↗</span></a>
						<?php endforeach; ?>
					</nav>
				<?php endif; ?>
			</div>
		</div>
	</section>
</main>
<?php get_footer(); ?>
