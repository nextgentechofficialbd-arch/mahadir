<?php
/** Fallback posts index. */
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}
get_header();
?>
<main id="main-content" class="site-main simple-page">
	<div class="wrap simple-page__wrap">
		<div class="section-label"><span>—</span><span><?php esc_html_e( 'Updates', 'global-computer-portfolio' ); ?></span></div>
		<h1 class="simple-entry__title"><?php esc_html_e( 'Notes & updates', 'global-computer-portfolio' ); ?></h1>
		<?php if ( have_posts() ) : ?>
			<div class="post-list">
				<?php while ( have_posts() ) : the_post(); ?>
					<article <?php post_class( 'post-list__item' ); ?>>
						<span class="post-list__date"><?php echo esc_html( get_the_date() ); ?></span>
						<div><h2><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h2><?php if ( has_excerpt() ) : ?><p><?php echo esc_html( get_the_excerpt() ); ?></p><?php endif; ?></div>
						<a class="post-list__arrow" href="<?php the_permalink(); ?>" aria-label="<?php echo esc_attr( sprintf( __( 'Read %s', 'global-computer-portfolio' ), get_the_title() ) ); ?>">↗</a>
					</article>
				<?php endwhile; ?>
			</div>
			<?php the_posts_pagination(); ?>
		<?php else : ?>
			<p><?php esc_html_e( 'There are no posts to show yet.', 'global-computer-portfolio' ); ?></p>
		<?php endif; ?>
	</div>
</main>
<?php get_footer(); ?>
