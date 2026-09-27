<?php
/** Default page template. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
get_header();
?>
<main id="main-content" class="site-main simple-page">
	<div class="wrap simple-page__wrap">
		<?php while ( have_posts() ) : the_post(); ?>
			<div class="breadcrumb"><a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php esc_html_e( 'Home', 'global-computer-portfolio' ); ?></a><span aria-hidden="true">/</span><span><?php the_title(); ?></span></div>
			<article <?php post_class( 'simple-entry' ); ?>>
				<h1 class="simple-entry__title"><?php the_title(); ?></h1>
				<div class="entry-content"><?php the_content(); ?></div>
			</article>
		<?php endwhile; ?>
	</div>
</main>
<?php get_footer(); ?>
