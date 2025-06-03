import '@blocknote/core/fonts/inter.css';
import { BlockNoteView } from '@blocknote/mantine';
import '@blocknote/mantine/style.css';
import { useEffect } from 'react';
import { createOpenAICompatible } from '@ai-sdk/openai-compatible';
import { OPENAI_API_BASE_URL } from '$lib/constants';
import { en } from '@blocknote/core/locales';
import { en as aiEn } from '@blocknote/xl-ai/locales';
import {
  FormattingToolbar,
  FormattingToolbarController,
  SuggestionMenuController,
  getDefaultReactSlashMenuItems,
  getFormattingToolbarItems,
  useCreateBlockNote,
} from "@blocknote/react";
import { filterSuggestionItems, BlockNoteEditor } from '@blocknote/core';
import {
  AIMenuController,
  AIToolbarButton,
  createAIExtension,
  getAISlashMenuItems,
} from "@blocknote/xl-ai";
import '@blocknote/xl-ai/style.css'; // add the AI stylesheet

console.log('OPENAI_API_BASE_URL', OPENAI_API_BASE_URL);

const provider = createOpenAICompatible({
	baseURL: "http://localhost:8080/api",
	name: 'abert-etalab',
	apiKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjEwN2QxMGM0LTU5MWYtNGI0My1hMjNmLTZlYzFkNWZkYmQ2OSJ9.5LD2Xsb29iC0RVPPJNgFX9fOPeHX0HiWGEe46lBUrKs'
});

const model = provider('albert-small');


export default function BlockNote({ content }: { content: string }) {
	// Creates a new editor instance.
	const editor = useCreateBlockNote({
		dictionary: {
			...en,
			ai: aiEn
		},
		extensions: [
			createAIExtension({
				model,
        stream: false
			})
		]
	});

	useEffect(() => {
		const replaceBlocks = async () => {
			editor.replaceBlocks(editor.document, await editor.tryParseMarkdownToBlocks(content));
		};
		replaceBlocks();
    
	}, []);

  console.log("something !!!!")
	// Renders the editor instance using a React component.
	return (
		<BlockNoteView
			theme={'light'}
			editor={editor}
			formattingToolbar={false}
			slashMenu={false}
		>
			{/* Add the AI Command menu to the editor */}
			<AIMenuController />

			{/* Create you own Formatting Toolbar with an AI button,
    (see the full example code below) */}
			<FormattingToolbarWithAI />

			{/* Create you own SlashMenu with an AI option,
    (see the full example code below) */}
			<SuggestionMenuWithAI editor={editor} />
		</BlockNoteView>
	);
}


function FormattingToolbarWithAI() {
  return (
    <FormattingToolbarController
      formattingToolbar={() => (
        <FormattingToolbar>
          {...getFormattingToolbarItems()}
          {/* Add the AI button */}
          <AIToolbarButton />
        </FormattingToolbar>
      )}
    />
  );
}
 
// Slash menu with the AI option added
function SuggestionMenuWithAI(props: {
  editor: BlockNoteEditor<any, any, any>;
}) {
  return (
    <SuggestionMenuController
      triggerCharacter="/"
      getItems={async (query) =>
        filterSuggestionItems(
          [
            ...getDefaultReactSlashMenuItems(props.editor),
            // add the default AI slash menu items, or define your own
            ...getAISlashMenuItems(props.editor),
          ],
          query,
        )
      }
    />
  );
}