import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FlashcardsData } from '@/types';
import { ChevronLeft, ChevronRight, Shuffle } from 'lucide-react';
import { Button } from '@/components/common/Button';

interface FlashcardViewerProps {
  data: FlashcardsData;
}

export const FlashcardViewer: React.FC<FlashcardViewerProps> = ({ data }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [cards, setCards] = useState(data.flashcards);

  const currentCard = cards[currentIndex];

  const handleNext = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1) % cards.length);
  };

  const handlePrevious = () => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 + cards.length) % cards.length);
  };

  const handleShuffle = () => {
    const shuffled = [...cards].sort(() => Math.random() - 0.5);
    setCards(shuffled);
    setCurrentIndex(0);
    setIsFlipped(false);
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-600">
          Card {currentIndex + 1} of {cards.length}
        </span>
        <Button variant="secondary" size="sm" onClick={handleShuffle}>
          <Shuffle className="h-4 w-4 mr-2" />
          Shuffle
        </Button>
      </div>

      {/* Flashcard */}
      <div
        onClick={() => setIsFlipped(!isFlipped)}
        className="relative h-64 cursor-pointer perspective"
      >
        <div
          className={`w-full h-full transition-transform duration-500 transform-style-3d ${
            isFlipped ? 'rotate-y-180' : ''
          }`}
        >
          {/* Front */}
          <div className="absolute w-full h-full backface-hidden bg-white rounded-lg shadow-lg p-8 flex items-center justify-center border-2 border-primary-200 overflow-y-auto">
            <div className="text-center w-full">
              <p className="text-sm text-gray-500 mb-3 font-semibold">Question</p>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentCard.question}</ReactMarkdown>
              </div>
            </div>
          </div>

          {/* Back */}
          <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-primary-50 rounded-lg shadow-lg p-8 flex items-center justify-center border-2 border-primary-200 overflow-y-auto">
            <div className="text-center w-full">
              <p className="text-sm text-primary-600 mb-3 font-semibold">Answer</p>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{currentCard.answer}</ReactMarkdown>
              </div>
            </div>
          </div>
        </div>
      </div>

      <p className="text-center text-sm text-gray-500">Click card to flip</p>

      {/* Navigation */}
      <div className="flex justify-center space-x-4">
        <Button variant="secondary" onClick={handlePrevious} disabled={cards.length <= 1}>
          <ChevronLeft className="h-5 w-5" />
        </Button>
        <Button variant="secondary" onClick={handleNext} disabled={cards.length <= 1}>
          <ChevronRight className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
};
