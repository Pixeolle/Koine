// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import tailwindcss from '@tailwindcss/vite';
import svelte from '@astrojs/svelte';
import node from '@astrojs/node'

// https://astro.build/config
export default defineConfig({
	output: 'server',
	adapter: node({ mode: 'standalone' }),
	integrations: [
		starlight({
			title: 'Koine',
			prerender: false,
			customCss: [
				'./src/styles/global.css'
			]
		}),
		svelte()
	],
	vite: {
		plugins: [tailwindcss()],
		ssr: {
			noExternal: ['markdown-it-container', 'shiki', '@shikijs/core']
		}
	},
});
