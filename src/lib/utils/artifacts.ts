import { dynamicArtifacts, showArtifacts, showControls } from '$lib/stores';
import { dynamicArtifactsHidden, forceSelectDynamicArtifacts } from '$lib/stores';

export interface ArtifactData {
	type: 'iframe' | 'svg' | 'text' | 'image' | 'file';
	content: string;
	title?: string;
	chatId?: string;
	messageId?: string;
}

/**
 * Émet un artefact via l'event emitter
 * 
 * Exemples d'utilisation :
 * 
 * // Afficher du texte
 * await __event_emitter__({
 *   'type': 'artifacts', 
 *   'data': {
 *     type: 'text',
 *     content: 'Voici un message important...',
 *     title: 'Notification'
 *   }
 * })
 * 
 * // Afficher une image
 * await __event_emitter__({
 *   'type': 'artifacts',
 *   'data': {
 *     type: 'image',
 *     content: 'https://example.com/image.png',
 *     title: 'Graphique des résultats'
 *   }
 * })
 * 
 * // Afficher du HTML personnalisé
 * await __event_emitter__({
 *   'type': 'artifacts',
 *   'data': {
 *     type: 'iframe',
 *     content: '<!DOCTYPE html><html><body><h1>Mon titre</h1><p>Mon contenu</p></body></html>',
 *     title: 'Page personnalisée'
 *   }
 * })
 * 
 * // Afficher un fichier à télécharger
 * await __event_emitter__({
 *   'type': 'artifacts',
 *   'data': {
 *     type: 'file',
 *     content: 'data:text/csv;base64,UEsDBBQAAAAIAA...',
 *     title: 'Rapport.csv'
 *   }
 * })
 */
export function emitArtifact(artifactData: ArtifactData) {
	console.log('=== EMIT ARTIFACT CALLED ===');
	console.log('Input data:', artifactData);
	
	const artifact = {
		id: crypto.randomUUID(),
		...artifactData,
		timestamp: Date.now()
	};
	
	console.log('Created artifact:', artifact);

	// Ajouter l'artefact au store
	dynamicArtifacts.update(artifacts => {
		console.log('Previous artifacts:', artifacts);
		const newArtifacts = [...artifacts, artifact];
		console.log('New artifacts array:', newArtifacts);
		return newArtifacts;
	});

	// Rendre visibles les artefacts dynamiques et forcer la sélection dynamique
	dynamicArtifactsHidden.set(false);
	forceSelectDynamicArtifacts.set(true);

	// Afficher automatiquement les artefacts
	console.log('Setting showArtifacts to true');
	showArtifacts.set(true);
	
	// ACTIVER AUSSI showControls pour afficher le composant
	console.log('Setting showControls to true');
	showControls.set(true);
	
	console.log('=== END EMIT ARTIFACT ===');
	return artifact.id;
}

/**
 * Supprime un artefact par son ID
 */
export function removeArtifact(artifactId: string) {
	dynamicArtifacts.update(artifacts => {
		const filteredArtifacts = artifacts.filter(artifact => artifact.id !== artifactId);
		
		// Si plus d'artifacts dynamiques, masquer l'interface
		if (filteredArtifacts.length === 0) {
			showArtifacts.set(false);
			showControls.set(false);
		}
		
		return filteredArtifacts;
	});
}

/**
 * Efface tous les artefacts dynamiques
 */
export function clearDynamicArtifacts() {
	dynamicArtifacts.set([]);
}

/**
 * Obtient un artefact par son ID
 */
export function getArtifact(artifactId: string) {
	let artifact = null;
	dynamicArtifacts.subscribe(artifacts => {
		artifact = artifacts.find(a => a.id === artifactId);
	})();
	return artifact;
} 