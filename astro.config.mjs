// @ts-check

import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { defineConfig, fontProviders } from 'astro/config';

/**
 * v3.0.8 안전망: CommonMark Right-flanking Delimiter 파싱 실패 방어
 *
 * 문제: CommonMark 사양 상 **text**조사 처럼 닫는 ** 바로 뒤에
 * 한국어(Unicode Letter)가 공백 없이 붙으면 파서가 닫는 기호로
 * 인식하지 못하고 날것의 별표를 HTML에 노출시킵니다.
 *
 * 해결: Vite transform 단계에서 원시 마크다운 파일을 remark/CommonMark가
 * 읽기 전에 해당 패턴을 HTML 태그로 미리 변환합니다.
 * 이로써 파서 충돌이 구조적으로 원천 차단됩니다.
 */
const koreanDelimiterFix = {
	name: 'korean-delimiter-preprocessor',
	/** @param {string} code @param {string} id */
	transform(code, id) {
		if (!id.match(/\.mdx?(\?|$)/)) return null;
		const fixed = code
			// **bold**조사 → <strong>bold</strong>조사
			.replace(/\*\*([^*\n]+?)\*\*([가-힣])/g, '<strong>$1</strong>$2')
			// *italic*조사 → <em>italic</em>조사 (단, **는 제외)
			.replace(/(?<!\*)\*([^*\n]+?)\*(?!\*)([가-힣])/g, '<em>$1</em>$2');
		if (fixed === code) return null;
		return { code: fixed, map: null };
	},
};

// https://astro.build/config
export default defineConfig({
	site: 'https://lumeninsights.kr',
	integrations: [mdx(), sitemap()],
	vite: {
		plugins: [koreanDelimiterFix],
	},
	fonts: [
		{
			provider: fontProviders.local(),
			name: 'Atkinson',
			cssVariable: '--font-atkinson',
			fallbacks: ['sans-serif'],
			options: {
				variants: [
					{
						src: ['./src/assets/fonts/atkinson-regular.woff'],
						weight: 400,
						style: 'normal',
						display: 'swap',
					},
					{
						src: ['./src/assets/fonts/atkinson-bold.woff'],
						weight: 700,
						style: 'normal',
						display: 'swap',
					},
				],
			},
		},
	],
});
