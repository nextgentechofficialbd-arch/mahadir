<?php
/** Single post and portfolio-project template. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
get_header();
?>
<main id="main-content" class="site-main simple-page">
	<div class="wrap simple-page__wrap">
		<div class="breadcrumb"><a href="<?php echo esc_url( home_url( '/' ) ); ?>"><?php esc_html_e( 'Home', 'global-computer-portfolio' ); ?></a><span aria-hidden="true">/</span><span><?php esc_html_e( 'Project', 'global-computer-portfolio' ); ?></span></div>
		<?php while ( have_posts() ) : the_post(); ?>
			<article <?php post_class( 'simple-entry' ); ?>>
				<p class="eyebrow"><span class="eyebrow__rule" aria-hidden="true"></span><?php esc_html_e( 'Portfolio project', 'global-computer-portfolio' ); ?></p>
				<h1 class="simple-entry__title"><?php the_title(); ?></h1>
				<?php if ( has_excerpt() ) : ?><p class="simple-entry__intro"><?php echo esc_html( get_the_excerpt() ); ?></p><?php endif; ?>
				<?php if ( has_post_thumbnail() ) : ?><div class="simple-entry__image"><?php the_post_thumbnail( 'large' ); ?></div><?php endif; ?>
				<div class="entry-content"><?php the_content(); ?></div>
			</article>
		<?php endwhile; ?>
		<a class="text-link text-link--underlined" href="<?php echo esc_url( home_url( '/' ) . '#projects' ); ?>"><?php esc_html_e( 'Back to the portfolio', 'global-computer-portfolio' ); ?><span aria-hidden="true">↗</span></a>
	</div>
</main>
<?php get_footer(); ?>
